package ui

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/d3ej/netgotchi/internal/pet"
	"github.com/d3ej/netgotchi/internal/styles"
	"github.com/d3ej/netgotchi/internal/tools"
)

type scanPhase int

const (
	scanPhaseTarget scanPhase = iota
	scanPhaseType
	scanPhaseCustom
	scanPhaseWaiting
	scanPhaseResult
)

var scanPresets = []string{"127.0.0.1", "192.168.1.0/24", "10.0.0.0/24", "CUSTOM", "BACK"}
var scanTypes = []string{"quick (ping)", "ports (TCP)", "full (sV -F)"}
var scanTypeKeys = []tools.ScanType{tools.ScanQuick, tools.ScanPorts, tools.ScanFull}

type scannerModel struct {
	p            *pet.Pet
	phase        scanPhase
	targetCursor int
	typeCursor   int
	input        textinput.Model
	spinner      spinner.Model
	target       string
	result       *tools.ToolResult
	scrollOffset int
	width        int
	height       int
}

func newScannerModel(p *pet.Pet, w, h int) scannerModel {
	ti := textinput.New()
	ti.Placeholder = "IP, range, or hostname"
	ti.CharLimit = 128
	ti.Width = 34

	s := spinner.New()
	s.Spinner = spinner.Globe
	s.Style = lipgloss.NewStyle().Foreground(styles.ColCyan)

	return scannerModel{p: p, input: ti, spinner: s, width: w, height: h}
}

func (m scannerModel) init() tea.Cmd { return nil }

func (m scannerModel) update(msg tea.Msg) (scannerModel, tea.Cmd) {
	switch m.phase {
	case scanPhaseTarget:
		return m.updateTarget(msg)
	case scanPhaseType:
		return m.updateType(msg)
	case scanPhaseCustom:
		return m.updateCustom(msg)
	case scanPhaseWaiting:
		return m.updateWaiting(msg)
	case scanPhaseResult:
		return m.updateResult(msg)
	}
	return m, nil
}

func (m scannerModel) updateTarget(msg tea.Msg) (scannerModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.targetCursor > 0 {
				m.targetCursor--
			}
		case "down", "j":
			if m.targetCursor < len(scanPresets)-1 {
				m.targetCursor++
			}
		case "enter", " ":
			choice := scanPresets[m.targetCursor]
			switch choice {
			case "BACK":
				return m, cmdBack()
			case "CUSTOM":
				m.phase = scanPhaseCustom
				m.input.Focus()
				m.input.SetValue("")
				return m, textinput.Blink
			default:
				m.target = choice
				m.phase = scanPhaseType
			}
		case "esc", "q":
			return m, cmdBack()
		}
	}
	return m, nil
}

func (m scannerModel) updateType(msg tea.Msg) (scannerModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.typeCursor > 0 {
				m.typeCursor--
			}
		case "down", "j":
			if m.typeCursor < len(scanTypes)-1 {
				m.typeCursor++
			}
		case "enter", " ":
			return m.startScan()
		case "esc", "q":
			m.phase = scanPhaseTarget
		}
	}
	return m, nil
}

func (m scannerModel) updateCustom(msg tea.Msg) (scannerModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "enter":
			t := strings.TrimSpace(m.input.Value())
			if t != "" {
				m.target = t
				m.phase = scanPhaseType
				return m, nil
			}
		case "esc":
			m.phase = scanPhaseTarget
			m.input.Blur()
			return m, nil
		}
	}
	var cmd tea.Cmd
	m.input, cmd = m.input.Update(msg)
	return m, cmd
}

func (m scannerModel) updateWaiting(msg tea.Msg) (scannerModel, tea.Cmd) {
	switch msg := msg.(type) {
	case scanResultMsg:
		m.result = &msg.result
		m.phase = scanPhaseResult
		m.scrollOffset = 0

		// Award pet XP / feed
		if hosts, ok := msg.result.Data["host_count"].(int); ok {
			m.p.ReactToScan(hosts)
		}
		return m, nil
	}
	var cmd tea.Cmd
	m.spinner, cmd = m.spinner.Update(msg)
	return m, cmd
}

func (m scannerModel) updateResult(msg tea.Msg) (scannerModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.scrollOffset > 0 {
				m.scrollOffset--
			}
		case "down", "j":
			m.scrollOffset++
		case "enter", "esc", "q":
			m.phase = scanPhaseTarget
			m.result = nil
		}
	}
	return m, nil
}

func (m scannerModel) startScan() (scannerModel, tea.Cmd) {
	scanType := scanTypeKeys[m.typeCursor]
	target := m.target
	m.phase = scanPhaseWaiting
	return m, tea.Batch(
		m.spinner.Tick,
		func() tea.Msg {
			return scanResultMsg{result: tools.RunScan(target, scanType)}
		},
	)
}

func (m scannerModel) view() string {
	var sb strings.Builder
	innerW := 38

	header := styles.ToolHeader.Width(innerW).Align(lipgloss.Center).Render("NMAP SCANNER")
	sb.WriteString(header)
	sb.WriteByte('\n')
	sb.WriteString(styles.Separator(innerW))
	sb.WriteByte('\n')

	switch m.phase {
	case scanPhaseTarget:
		sb.WriteString(styles.Dim.Render("Select target:"))
		sb.WriteByte('\n')
		for i, t := range scanPresets {
			if i == m.targetCursor {
				sb.WriteString(styles.Selected.Render(fmt.Sprintf("  ▸ %s", t)))
			} else {
				sb.WriteString(styles.Normal.Render(fmt.Sprintf("    %s", t)))
			}
			sb.WriteByte('\n')
		}
		sb.WriteString(styles.Hint.Render("↑↓ nav  ↵ select  esc back"))

	case scanPhaseType:
		sb.WriteString(styles.Cyan.Render(fmt.Sprintf("Target: %s", m.target)))
		sb.WriteByte('\n')
		sb.WriteString(styles.Dim.Render("Scan type:"))
		sb.WriteByte('\n')
		for i, t := range scanTypes {
			if i == m.typeCursor {
				sb.WriteString(styles.Selected.Render(fmt.Sprintf("  ▸ %s", t)))
			} else {
				sb.WriteString(styles.Normal.Render(fmt.Sprintf("    %s", t)))
			}
			sb.WriteByte('\n')
		}
		sb.WriteString(styles.Hint.Render("↑↓ nav  ↵ scan  esc back"))

	case scanPhaseCustom:
		sb.WriteString(styles.Dim.Render("Enter target (IP / CIDR / hostname):"))
		sb.WriteByte('\n')
		sb.WriteString(m.input.View())
		sb.WriteByte('\n')
		sb.WriteString(styles.Hint.Render("↵ next  esc back"))

	case scanPhaseWaiting:
		sb.WriteString(m.spinner.View())
		sb.WriteString(styles.Cyan.Render(fmt.Sprintf("  Scanning %s…", m.target)))
		sb.WriteByte('\n')
		sb.WriteString(styles.Dim.Render("(this may take a while)"))

	case scanPhaseResult:
		sb.WriteString(m.viewResult())
	}

	return styles.AppBox.Width(44).Render(sb.String())
}

func (m scannerModel) viewResult() string {
	r := m.result
	var sb strings.Builder

	hostCount := 0
	var hosts []tools.ScanHost
	if r.Success {
		if hc, ok := r.Data["host_count"].(int); ok {
			hostCount = hc
		}
		if hs, ok := r.Data["hosts"].([]tools.ScanHost); ok {
			hosts = hs
		}
	}

	if r.Success {
		sb.WriteString(styles.Green.Render(fmt.Sprintf("● Scan complete — %d host(s) up", hostCount)))
	} else {
		sb.WriteString(styles.Red.Render("✗ Scan failed"))
		sb.WriteByte('\n')
		sb.WriteString(styles.Dim.Render(truncate(r.Error, 40)))
		sb.WriteByte('\n')
		sb.WriteString(styles.Hint.Render("↵ / esc  back"))
		return sb.String()
	}

	sb.WriteByte('\n')
	sb.WriteString(styles.Dim.Render(fmt.Sprintf("Time: %.1fs  +%d XP", r.Duration, r.XPReward)))
	sb.WriteByte('\n')
	sb.WriteString(styles.Dim.Render(strings.Repeat("─", 38)))
	sb.WriteByte('\n')

	// Scrollable host list
	maxVisible := 8
	if m.scrollOffset > len(hosts)-maxVisible && len(hosts) > maxVisible {
		m.scrollOffset = len(hosts) - maxVisible
	}
	start := m.scrollOffset
	if start < 0 {
		start = 0
	}
	end := start + maxVisible
	if end > len(hosts) {
		end = len(hosts)
	}

	for _, h := range hosts[start:end] {
		label := h.IP
		if h.Hostname != "" {
			label = fmt.Sprintf("%s (%s)", h.Hostname, h.IP)
		}
		sb.WriteString(styles.Cyan.Render("  ◎ " + label))
		sb.WriteByte('\n')
		for _, p := range h.Ports {
			svc := p.Service
			if p.Version != "" {
				svc += " " + p.Version
			}
			sb.WriteString(styles.Dim.Render(fmt.Sprintf("    %d/%s  %s", p.Port, p.Protocol, svc)))
			sb.WriteByte('\n')
		}
	}

	if len(hosts) > maxVisible {
		sb.WriteString(styles.Hint.Render(fmt.Sprintf("↑↓ scroll  %d/%d", end, len(hosts))))
		sb.WriteByte('\n')
	}
	sb.WriteString(styles.Hint.Render("↵ / esc  back to targets"))
	return sb.String()
}
