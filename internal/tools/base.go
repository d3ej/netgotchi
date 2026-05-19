// Package tools provides the network tool implementations: ping, SSH, and nmap.
package tools

// ToolResult is the outcome of any network tool execution.
type ToolResult struct {
	ToolName string
	Success  bool
	Data     map[string]any
	Error    string
	Duration float64 // seconds
	XPReward int
}
