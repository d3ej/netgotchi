package tools

import "testing"

const sampleNmapXML = `<?xml version="1.0"?>
<nmaprun>
  <host>
    <status state="up"/>
    <address addr="192.168.1.10" addrtype="ipv4"/>
    <hostnames><hostname name="router.lan"/></hostnames>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh" version="OpenSSH 9.0"/>
      </port>
      <port protocol="tcp" portid="80">
        <state state="closed"/>
        <service name="http"/>
      </port>
    </ports>
  </host>
  <host>
    <status state="down"/>
    <address addr="192.168.1.11" addrtype="ipv4"/>
  </host>
</nmaprun>
`

func TestParseNmapXML(t *testing.T) {
	hosts := parseNmapXML([]byte(sampleNmapXML))

	if len(hosts) != 1 {
		t.Fatalf("got %d hosts, want 1 (down host should be excluded)", len(hosts))
	}

	h := hosts[0]
	if h.IP != "192.168.1.10" {
		t.Errorf("IP = %q, want 192.168.1.10", h.IP)
	}
	if h.Hostname != "router.lan" {
		t.Errorf("Hostname = %q, want router.lan", h.Hostname)
	}
	if len(h.Ports) != 1 {
		t.Fatalf("got %d open ports, want 1 (closed port should be excluded)", len(h.Ports))
	}
	if h.Ports[0].Port != 22 || h.Ports[0].Service != "ssh" {
		t.Errorf("port = %+v, want 22/ssh", h.Ports[0])
	}
}

func TestParseNmapXMLInvalid(t *testing.T) {
	hosts := parseNmapXML([]byte("not xml"))
	if hosts != nil {
		t.Errorf("hosts = %v, want nil on parse failure", hosts)
	}
}

func TestBuildNmapArgs(t *testing.T) {
	cases := []struct {
		scanType ScanType
		want     []string
	}{
		{ScanQuick, []string{"-sn", "10.0.0.1"}},
		{ScanPorts, []string{"-sT", "10.0.0.1"}},
		{ScanFull, []string{"-sT", "-sV", "-F", "10.0.0.1"}},
	}
	for _, c := range cases {
		got := buildNmapArgs("10.0.0.1", c.scanType)
		if len(got) != len(c.want) {
			t.Fatalf("buildNmapArgs(%v) = %v, want %v", c.scanType, got, c.want)
		}
		for i := range c.want {
			if got[i] != c.want[i] {
				t.Errorf("buildNmapArgs(%v)[%d] = %q, want %q", c.scanType, i, got[i], c.want[i])
			}
		}
	}
}
