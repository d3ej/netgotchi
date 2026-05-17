package tools

import (
	"os/exec"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"time"
)

var (
	rttRE  = regexp.MustCompile(`min/avg/max[^=]*= [\d.]+/([\d.]+)/[\d.]+`)
	lossRE = regexp.MustCompile(`(\d+)% packet loss`)

	// Windows variants
	rttREWin  = regexp.MustCompile(`Average = (\d+)ms`)
	lossREWin = regexp.MustCompile(`\((\d+)% loss\)`)
)

// RunPing executes the system ping command and returns a ToolResult.
func RunPing(target string, count int) ToolResult {
	start := time.Now()

	args := buildPingArgs(target, count)
	cmd := exec.Command("ping", args...)
	out, err := cmd.CombinedOutput()
	raw := string(out)
	duration := time.Since(start).Seconds()

	if err != nil && len(out) == 0 {
		return ToolResult{
			ToolName: "ping",
			Success:  false,
			Error:    err.Error(),
			Duration: duration,
			XPReward: 5,
		}
	}

	rttAvg, loss := parsePingOutput(raw)
	success := loss < 100 && rttAvg >= 0

	xp := 5
	if success {
		xp = 10
		if rttAvg > 0 && rttAvg < 10 {
			xp = 15
		}
	}

	return ToolResult{
		ToolName: "ping",
		Success:  success,
		Data: map[string]any{
			"rtt_avg":    rttAvg,
			"packet_loss": loss,
			"raw_output": raw,
			"target":     target,
		},
		Duration: duration,
		XPReward: xp,
	}
}

func buildPingArgs(target string, count int) []string {
	c := strconv.Itoa(count)
	if runtime.GOOS == "windows" {
		return []string{"-n", c, target}
	}
	return []string{"-c", c, target}
}

func parsePingOutput(raw string) (rttAvg float64, loss int) {
	rttAvg = -1
	loss = 100

	if runtime.GOOS == "windows" {
		if m := rttREWin.FindStringSubmatch(raw); len(m) == 2 {
			v, _ := strconv.ParseFloat(m[1], 64)
			rttAvg = v
		}
		if m := lossREWin.FindStringSubmatch(raw); len(m) == 2 {
			v, _ := strconv.Atoi(m[1])
			loss = v
		}
		return
	}

	// Unix
	if m := rttRE.FindStringSubmatch(raw); len(m) == 2 {
		v, _ := strconv.ParseFloat(m[1], 64)
		rttAvg = v
	}
	if m := lossRE.FindStringSubmatch(raw); len(m) == 2 {
		v, _ := strconv.Atoi(m[1])
		loss = v
	}

	// Fallback: if "0 received" appears in a minimal output, mark 100% loss
	if rttAvg < 0 && strings.Contains(raw, "0 received") {
		loss = 100
	}
	return
}
