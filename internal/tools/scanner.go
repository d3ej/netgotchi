package tools

import (
	"encoding/xml"
	"fmt"
	"os/exec"
	"time"
)

// ScanType selects the nmap scan profile.
type ScanType string

const (
	ScanQuick ScanType = "quick" // ping scan only
	ScanPorts ScanType = "ports" // TCP connect scan
	ScanFull  ScanType = "full"  // TCP + version detection (fast flag set)
)

// ScanHost is one host found by nmap.
type ScanHost struct {
	IP       string
	Hostname string
	State    string
	Ports    []ScanPort
}

// ScanPort is one open port on a host.
type ScanPort struct {
	Port     int
	Protocol string
	State    string
	Service  string
	Version  string
}

// RunScan executes nmap and returns a ToolResult.
func RunScan(target string, scanType ScanType) ToolResult {
	start := time.Now()

	args := buildNmapArgs(target, scanType)
	args = append([]string{"-oX", "-"}, args...)
	cmd := exec.Command("nmap", args...)
	out, err := cmd.CombinedOutput()
	duration := time.Since(start).Seconds()

	if err != nil && len(out) == 0 {
		return ToolResult{
			ToolName: "nmap",
			Success:  false,
			Error:    fmt.Sprintf("nmap failed: %v", err),
			Duration: duration,
			XPReward: 0,
		}
	}

	hosts := parseNmapXML(out)
	xp := 10 + len(hosts)*5

	return ToolResult{
		ToolName: "nmap",
		Success:  true,
		Data: map[string]any{
			"hosts":      hosts,
			"host_count": len(hosts),
			"target":     target,
			"scan_type":  string(scanType),
		},
		Duration: duration,
		XPReward: xp,
	}
}

func buildNmapArgs(target string, t ScanType) []string {
	switch t {
	case ScanQuick:
		return []string{"-sn", target}
	case ScanPorts:
		return []string{"-sT", target}
	case ScanFull:
		return []string{"-sT", "-sV", "-F", target}
	default:
		return []string{"-sn", target}
	}
}

// --- XML parsing ---

type nmapRun struct {
	XMLName xml.Name    `xml:"nmaprun"`
	Hosts   []nmapHost  `xml:"host"`
}

type nmapHost struct {
	Status    nmapStatus     `xml:"status"`
	Addresses []nmapAddress  `xml:"address"`
	Hostnames []nmapHostname `xml:"hostnames>hostname"`
	Ports     []nmapPort     `xml:"ports>port"`
}

type nmapStatus struct {
	State string `xml:"state,attr"`
}

type nmapAddress struct {
	Addr     string `xml:"addr,attr"`
	AddrType string `xml:"addrtype,attr"`
}

type nmapHostname struct {
	Name string `xml:"name,attr"`
}

type nmapPort struct {
	Protocol string      `xml:"protocol,attr"`
	PortID   int         `xml:"portid,attr"`
	State    nmapPState  `xml:"state"`
	Service  nmapService `xml:"service"`
}

type nmapPState struct {
	State string `xml:"state,attr"`
}

type nmapService struct {
	Name    string `xml:"name,attr"`
	Version string `xml:"version,attr"`
}

func parseNmapXML(data []byte) []ScanHost {
	var run nmapRun
	if err := xml.Unmarshal(data, &run); err != nil {
		return nil
	}

	var result []ScanHost
	for _, h := range run.Hosts {
		if h.Status.State != "up" {
			continue
		}
		sh := ScanHost{State: h.Status.State}
		for _, a := range h.Addresses {
			if a.AddrType == "ipv4" || a.AddrType == "ipv6" {
				sh.IP = a.Addr
				break
			}
		}
		if len(h.Hostnames) > 0 {
			sh.Hostname = h.Hostnames[0].Name
		}
		for _, p := range h.Ports {
			if p.State.State != "open" {
				continue
			}
			sh.Ports = append(sh.Ports, ScanPort{
				Port:     p.PortID,
				Protocol: p.Protocol,
				State:    p.State.State,
				Service:  p.Service.Name,
				Version:  p.Service.Version,
			})
		}
		result = append(result, sh)
	}
	return result
}
