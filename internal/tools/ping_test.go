package tools

import "testing"

const linuxPingOutput = `PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=113 time=12.3 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=113 time=12.4 ms

--- 8.8.8.8 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3005ms
rtt min/avg/max/mdev = 11.802/12.345/13.100/0.500 ms
`

const linuxPingOutputAllLost = `PING 10.255.255.1 (10.255.255.1) 56(84) bytes of data.

--- 10.255.255.1 ping statistics ---
4 packets transmitted, 0 received, 100% packet loss, time 3060ms
`

func TestParsePingOutputSuccess(t *testing.T) {
	rtt, loss := parsePingOutput(linuxPingOutput)

	if rtt != 12.345 {
		t.Errorf("rtt = %v, want 12.345", rtt)
	}
	if loss != 0 {
		t.Errorf("loss = %d, want 0", loss)
	}
}

func TestParsePingOutputAllLost(t *testing.T) {
	rtt, loss := parsePingOutput(linuxPingOutputAllLost)

	if loss != 100 {
		t.Errorf("loss = %d, want 100", loss)
	}
	if rtt >= 0 {
		t.Errorf("rtt = %v, want negative sentinel when no reply parsed", rtt)
	}
}

func TestParsePingOutputGarbage(t *testing.T) {
	rtt, loss := parsePingOutput("not ping output at all")

	if rtt != -1 {
		t.Errorf("rtt = %v, want -1 sentinel", rtt)
	}
	if loss != 100 {
		t.Errorf("loss = %d, want 100 sentinel", loss)
	}
}

func TestBuildPingArgsUnix(t *testing.T) {
	args := buildPingArgs("example.com", 4)
	want := []string{"-c", "4", "example.com"}
	if len(args) != len(want) {
		t.Fatalf("args = %v, want %v", args, want)
	}
	for i := range want {
		if args[i] != want[i] {
			t.Errorf("args[%d] = %q, want %q", i, args[i], want[i])
		}
	}
}
