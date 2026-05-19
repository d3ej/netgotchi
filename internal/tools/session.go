package tools

import "time"

// DiscoveredHost is a network host aggregated from one or more tool runs.
type DiscoveredHost struct {
	IP           string     `json:"ip"                     yaml:"ip"`
	Hostname     string     `json:"hostname,omitempty"     yaml:"hostname,omitempty"`
	State        string     `json:"state"                  yaml:"state"`
	Ports        []ScanPort `json:"ports,omitempty"        yaml:"ports,omitempty"`
	RTTMs        float64    `json:"rtt_ms,omitempty"       yaml:"rtt_ms,omitempty"`
	SSHUser      string     `json:"ssh_user,omitempty"     yaml:"ssh_user,omitempty"`
	Tags         []string   `json:"tags"                   yaml:"tags"`
	Sources      []string   `json:"sources"                yaml:"sources"`
	DiscoveredAt time.Time  `json:"discovered_at"          yaml:"discovered_at"`
}

// ScanSession accumulates network discovery data within one application run.
// All access is from the Bubbletea main goroutine (via tea.Msg handlers),
// so no synchronisation is required.
type ScanSession struct {
	StartedAt time.Time
	hosts     map[string]*DiscoveredHost // keyed by IP address
}

// NewScanSession initialises an empty session.
func NewScanSession() *ScanSession {
	return &ScanSession{
		StartedAt: time.Now(),
		hosts:     make(map[string]*DiscoveredHost),
	}
}

// AddPingResult merges a successful ping result into the session.
func (s *ScanSession) AddPingResult(r ToolResult) {
	if !r.Success {
		return
	}
	ip, _ := r.Data["target"].(string)
	if ip == "" {
		return
	}
	h := s.upsert(ip)
	if rtt, ok := r.Data["rtt_avg"].(float64); ok && rtt >= 0 {
		h.RTTMs = rtt
	}
	h.State = "up"
	h.addSource("ping")
}

// AddScanResult merges nmap scan hosts into the session.
func (s *ScanSession) AddScanResult(r ToolResult) {
	if !r.Success {
		return
	}
	hosts, ok := r.Data["hosts"].([]ScanHost)
	if !ok {
		return
	}
	for _, sh := range hosts {
		h := s.upsert(sh.IP)
		if sh.Hostname != "" {
			h.Hostname = sh.Hostname
		}
		h.State = sh.State
		if len(sh.Ports) > 0 {
			h.Ports = sh.Ports
		}
		h.addSource("nmap")
	}
}

// AddSSHResult records a successful SSH connection in the session.
func (s *ScanSession) AddSSHResult(params SSHParams) {
	h := s.upsert(params.Host)
	if params.Username != "" {
		h.SSHUser = params.Username
	}
	h.State = "up"
	h.addSource("ssh")
}

// HostCount returns the number of unique hosts discovered so far.
func (s *ScanSession) HostCount() int { return len(s.hosts) }

// Hosts returns all discovered hosts as a snapshot slice.
func (s *ScanSession) Hosts() []DiscoveredHost {
	out := make([]DiscoveredHost, 0, len(s.hosts))
	for _, h := range s.hosts {
		out = append(out, *h)
	}
	return out
}

func (s *ScanSession) upsert(ip string) *DiscoveredHost {
	if h, ok := s.hosts[ip]; ok {
		return h
	}
	h := &DiscoveredHost{
		IP:           ip,
		State:        "unknown",
		Tags:         []string{"netgotchi"},
		Sources:      []string{},
		DiscoveredAt: time.Now(),
	}
	s.hosts[ip] = h
	return h
}

func (h *DiscoveredHost) addSource(src string) {
	for _, s := range h.Sources {
		if s == src {
			return
		}
	}
	h.Sources = append(h.Sources, src)
}
