package tools

import "testing"

func TestDiscoverHostsAlwaysIncludesLocalhost(t *testing.T) {
	hosts := DiscoverHosts()

	found := false
	for _, h := range hosts {
		if h.Addr == "127.0.0.1" && h.Port == 22 {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("DiscoverHosts() = %+v, want a 127.0.0.1:22 entry", hosts)
	}
}

func TestDiscoverHostsDedupesByAddr(t *testing.T) {
	hosts := DiscoverHosts()

	seen := map[string]bool{}
	for _, h := range hosts {
		if seen[h.Addr] {
			t.Errorf("duplicate addr %q in DiscoverHosts() result", h.Addr)
		}
		seen[h.Addr] = true
	}
}
