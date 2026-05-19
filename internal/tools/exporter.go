package tools

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"gopkg.in/yaml.v3"
)

// ExportFormat selects the output schema.
type ExportFormat int

const (
	ExportGenericJSON ExportFormat = iota
	ExportGenericYAML
	ExportNetBoxJSON
	ExportAnsibleYAML
)

// NetworkInventory is the neutral generic schema.
type NetworkInventory struct {
	Meta  InventoryMeta  `json:"meta"  yaml:"meta"`
	Hosts []DiscoveredHost `json:"hosts" yaml:"hosts"`
}

// InventoryMeta describes how and when the snapshot was produced.
type InventoryMeta struct {
	GeneratedAt time.Time `json:"generated_at" yaml:"generated_at"`
	HostCount   int       `json:"host_count"   yaml:"host_count"`
	Sources     []string  `json:"sources"      yaml:"sources"`
}

// Export writes a session snapshot in the chosen format to dir.
// Returns the absolute path of the created file.
// Files are created with 0o600 (owner read/write only).
// SSH passwords are never included in the output.
func Export(session *ScanSession, format ExportFormat, dir string) (string, error) {
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return "", fmt.Errorf("create export dir: %w", err)
	}

	ts := time.Now().Format("20060102-150405")
	var (
		filename string
		data     []byte
		err      error
	)

	switch format {
	case ExportGenericJSON:
		filename = fmt.Sprintf("netgotchi-%s.json", ts)
		data, err = encodeGenericJSON(session)
	case ExportGenericYAML:
		filename = fmt.Sprintf("netgotchi-%s.yaml", ts)
		data, err = encodeGenericYAML(session)
	case ExportNetBoxJSON:
		filename = fmt.Sprintf("netbox-%s.json", ts)
		data, err = encodeNetBoxJSON(session)
	case ExportAnsibleYAML:
		filename = fmt.Sprintf("ansible-%s.yaml", ts)
		data, err = encodeAnsibleYAML(session)
	default:
		return "", fmt.Errorf("unknown export format %d", format)
	}
	if err != nil {
		return "", err
	}

	path, _ := filepath.Abs(filepath.Join(dir, filename))
	if err := os.WriteFile(path, data, 0o600); err != nil {
		return "", fmt.Errorf("write %s: %w", path, err)
	}
	return path, nil
}

// ── helpers ───────────────────────────────────────────────────────────────────

func buildInventory(session *ScanSession) NetworkInventory {
	hosts := session.Hosts()
	seen := make(map[string]struct{})
	for _, h := range hosts {
		for _, s := range h.Sources {
			seen[s] = struct{}{}
		}
	}
	srcs := make([]string, 0, len(seen))
	for s := range seen {
		srcs = append(srcs, s)
	}
	return NetworkInventory{
		Meta: InventoryMeta{
			GeneratedAt: time.Now().UTC(),
			HostCount:   len(hosts),
			Sources:     srcs,
		},
		Hosts: hosts,
	}
}

func encodeGenericJSON(session *ScanSession) ([]byte, error) {
	return json.MarshalIndent(buildInventory(session), "", "  ")
}

func encodeGenericYAML(session *ScanSession) ([]byte, error) {
	return yaml.Marshal(buildInventory(session))
}

// ── NetBox format ─────────────────────────────────────────────────────────────

type netBoxBundle struct {
	Devices     []netBoxDevice    `json:"devices"`
	IPAddresses []netBoxIPAddress `json:"ip_addresses"`
	Services    []netBoxService   `json:"services"`
}

type netBoxDevice struct {
	Name   string        `json:"name"`
	Status string        `json:"status"`
	Tags   []netBoxTag   `json:"tags,omitempty"`
}

type netBoxIPAddress struct {
	Address string      `json:"address"`
	Status  string      `json:"status"`
	DNSName string      `json:"dns_name,omitempty"`
	Tags    []netBoxTag `json:"tags,omitempty"`
}

type netBoxService struct {
	Device   string `json:"device"`
	Name     string `json:"name"`
	Protocol string `json:"protocol"`
	Ports    []int  `json:"ports"`
}

type netBoxTag struct {
	Name string `json:"name"`
}

func encodeNetBoxJSON(session *ScanSession) ([]byte, error) {
	hosts := session.Hosts()
	bundle := netBoxBundle{
		Devices:     make([]netBoxDevice, 0, len(hosts)),
		IPAddresses: make([]netBoxIPAddress, 0, len(hosts)),
		Services:    []netBoxService{},
	}

	for _, h := range hosts {
		name := h.Hostname
		if name == "" {
			name = h.IP
		}
		status := "active"
		if h.State != "up" {
			status = "offline"
		}
		tags := make([]netBoxTag, 0, len(h.Tags))
		for _, t := range h.Tags {
			tags = append(tags, netBoxTag{Name: t})
		}

		bundle.Devices = append(bundle.Devices, netBoxDevice{
			Name: name, Status: status, Tags: tags,
		})
		bundle.IPAddresses = append(bundle.IPAddresses, netBoxIPAddress{
			Address: h.IP + "/32",
			Status:  status,
			DNSName: h.Hostname,
			Tags:    tags,
		})

		tcpPorts, udpPorts := []int{}, []int{}
		for _, p := range h.Ports {
			switch p.Protocol {
			case "tcp":
				tcpPorts = append(tcpPorts, p.Port)
			case "udp":
				udpPorts = append(udpPorts, p.Port)
			}
		}
		if len(tcpPorts) > 0 {
			bundle.Services = append(bundle.Services, netBoxService{
				Device: name, Name: "discovered-tcp", Protocol: "tcp", Ports: tcpPorts,
			})
		}
		if len(udpPorts) > 0 {
			bundle.Services = append(bundle.Services, netBoxService{
				Device: name, Name: "discovered-udp", Protocol: "udp", Ports: udpPorts,
			})
		}
	}

	return json.MarshalIndent(bundle, "", "  ")
}

// ── Ansible format ────────────────────────────────────────────────────────────

type ansibleInventory struct {
	All ansibleGroup `yaml:"all"`
}

type ansibleGroup struct {
	Hosts map[string]ansibleHostVars `yaml:"hosts"`
}

type ansibleHostVars struct {
	AnsibleHost string  `yaml:"ansible_host"`
	AnsibleUser string  `yaml:"ansible_user,omitempty"`
	Hostname    string  `yaml:"hostname,omitempty"`
	RTTMs       float64 `yaml:"rtt_ms,omitempty"`
	OpenPorts   []int   `yaml:"open_ports,omitempty"`
}

func encodeAnsibleYAML(session *ScanSession) ([]byte, error) {
	hosts := session.Hosts()
	inv := ansibleInventory{All: ansibleGroup{Hosts: make(map[string]ansibleHostVars, len(hosts))}}

	for _, h := range hosts {
		key := h.IP
		if h.Hostname != "" {
			key = h.Hostname
		}
		ports := make([]int, 0, len(h.Ports))
		for _, p := range h.Ports {
			ports = append(ports, p.Port)
		}
		vars := ansibleHostVars{
			AnsibleHost: h.IP,
			AnsibleUser: h.SSHUser,
			Hostname:    h.Hostname,
			RTTMs:       h.RTTMs,
		}
		if len(ports) > 0 {
			vars.OpenPorts = ports
		}
		inv.All.Hosts[key] = vars
	}

	return yaml.Marshal(inv)
}
