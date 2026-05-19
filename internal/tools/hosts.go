package tools

import (
	"bufio"
	"net"
	"os"
	"path/filepath"
	"strings"
)

// Host represents a discovered network target.
type Host struct {
	Name string
	Addr string
	User string
	Port int
}

// DiscoverHosts merges hosts from ~/.ssh/config and /etc/hosts.
// localhost is always included.
func DiscoverHosts() []Host {
	seen := map[string]bool{}
	var hosts []Host

	add := func(h Host) {
		if h.Addr == "" {
			h.Addr = h.Name
		}
		if h.Port == 0 {
			h.Port = 22
		}
		if seen[h.Addr] {
			return
		}
		seen[h.Addr] = true
		hosts = append(hosts, h)
	}

	// Always include localhost
	add(Host{Name: "localhost", Addr: "127.0.0.1", Port: 22})

	for _, h := range sshConfigHosts() {
		add(h)
	}
	for _, h := range etcHostsHosts() {
		add(h)
	}
	return hosts
}

func sshConfigHosts() []Host {
	home, err := os.UserHomeDir()
	if err != nil {
		return nil
	}
	f, err := os.Open(filepath.Join(home, ".ssh", "config"))
	if err != nil {
		return nil
	}
	defer f.Close()

	var hosts []Host
	var cur Host
	flush := func() {
		if cur.Name != "" && cur.Name != "*" {
			hosts = append(hosts, cur)
		}
		cur = Host{Port: 22}
	}

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) < 2 {
			continue
		}
		key, val := strings.ToLower(parts[0]), parts[1]
		switch key {
		case "host":
			flush()
			cur.Name = val
		case "hostname":
			cur.Addr = val
		case "user":
			cur.User = val
		case "port":
			var p int
			if _, err := parsePort(val, &p); err == nil {
				cur.Port = p
			}
		}
	}
	flush()
	return hosts
}

func parsePort(s string, dst *int) (string, error) {
	var p int
	_, err := parseScanInt(s, &p)
	if err != nil {
		return s, err
	}
	*dst = p
	return s, nil
}

func parseScanInt(s string, dst *int) (string, error) {
	n := 0
	for _, c := range s {
		if c < '0' || c > '9' {
			return s, &net.AddrError{Err: "not a number", Addr: s}
		}
		n = n*10 + int(c-'0')
	}
	*dst = n
	return s, nil
}

func etcHostsHosts() []Host {
	f, err := os.Open("/etc/hosts")
	if err != nil {
		return nil
	}
	defer f.Close()

	var hosts []Host
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		if idx := strings.Index(line, "#"); idx >= 0 {
			line = line[:idx]
		}
		fields := strings.Fields(line)
		if len(fields) < 2 {
			continue
		}
		addr := fields[0]
		// Skip loopback and link-local
		if strings.HasPrefix(addr, "127.") || addr == "::1" ||
			strings.HasPrefix(addr, "fe80:") || strings.HasPrefix(addr, "ff0") {
			continue
		}
		name := fields[1]
		hosts = append(hosts, Host{Name: name, Addr: addr, Port: 22})
	}
	return hosts
}
