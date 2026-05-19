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

type pingPhase int

const (
	pingPhaseMenu pingPhase = iota
	pingPhaseCustom
	pingPhaseWaiting
	pingPhaseResult
)

var pingPresets = []string{"8.8.8.8", "1.1.1.1", "127.0.0.1", "CUSTOM", "BACK"}

type pingModel struct {
	p       *pet.Pet
	phase   pingPhase
	cursor  int
	input   textinput.Model
	spinner spinner.Model
	result  *tools.ToolResult
	width   int
	height  int
}

func newPingModel(p *pet.Pet, w, h int) pingModel {
	ti := textinput.New()
	ti.Placeholder = "hostname or IP"
	ti.CharLimit = 253
	ti.Width = 30

	s := spinner.New()
	s.Spinner = spinner.Dot
	s.Style = lipgloss.NewStyle().Foreground(styles.ColYellow)

	return pingModel{p: p, input: ti, spinner: s, width: w, height: h}
}

func (m pingModel) init() tea.Cmd { return nil }

func (m pingModel) update(msg tea.Msg) (pingModel, tea.Cmd) {
	switch m.phase {
	case pingPhaseMenu:
		return m.updateMenu(msg)
	case pingPhaseCustom:
		return m.updateCustom(msg)
	case pingPhaseWaiting:
		return m.updateWaiting(msg)
	case pingPhaseResult:
		return m.updateResult(msg)
	}
	return m, nil
}

func (m pingModel) updateMenu(msg tea.Msg) (pingModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(pingPresets)-1 {
				m.cursor++
			}
		case "enter", " ":
			choice := pingPresets[m.cursor]
			switch choice {
			case "BACK":
				return m, cmdBack()
			case "CUSTOM":
				m.phase = pingPhaseCustom
				m.input.Focus()
				m.input.SetValue("")
				return m, textinput.Blink
			default:
				return m.startPing(choice)
			}
		case "esc", "q":
			return m, cmdBack()
		}
	}
	return m, nil
}

func (m pingModel) updateCustom(msg tea.Msg) (pingModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "enter":
			target := strings.TrimSpace(m.input.Value())
			if target != "" {
				return m.startPing(target)
			}
		case "esc":
			m.phase = pingPhaseMenu
			m.input.Blur()
			return m, nil
		}
	}
	var cmd tea.Cmd
	m.input, cmd = m.input.Update(msg)
	return m, cmd
}

func (m pingModel) updateWaiting(msg tea.Msg) (pingModel, tea.Cmd) {
	switch msg := msg.(type) {
	case pingResultMsg:
		m.result = &msg.result
		m.phase = pingPhaseResult
		// Award pet XP
		if msg.result.Success {
			rtt, _ := msg.result.Data["rtt_avg"].(float64)
			m.p.EarnXP(msg.result.XPReward, "ping")
			m.p.ReactToPing(true, rtt)
		} else {
			m.p.ReactToPing(false, 0)
		}
		return m, nil
	}
	var cmd tea.Cmd
	m.spinner, cmd = m.spinner.Update(msg)
	return m, cmd
}

func (m pingModel) updateResult(msg tea.Msg) (pingModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "enter", "esc", "q":
			// Reset to menu
			m.phase = pingPhaseMenu
			m.result = nil
			return m, nil
		}
	}
	return m, nil
}

func (m pingModel) startPing(target string) (pingModel, tea.Cmd) {
	m.phase = pingPhaseWaiting
	return m, tea.Batch(
		m.spinner.Tick,
		func() tea.Msg {
			return pingResultMsg{result: tools.RunPing(target, 4)}
		},
	)
}

func (m pingModel) view() string {
	var sb strings.Builder

	innerW := 36
	header := styles.ToolHeader.Width(innerW).Align(lipgloss.Center).Render("PING TOOL")
	sb.WriteString(header)
	sb.WriteByte('\n')
	sb.WriteString(styles.Separator(innerW))
	sb.WriteByte('\n')

	switch m.phase {
	case pingPhaseMenu:
		sb.WriteString(styles.Dim.Render("Select target:"))
		sb.WriteByte('\n')
		for i, target := range pingPresets {
			if i == m.cursor {
				sb.WriteString(styles.Selected.Render(fmt.Sprintf("  ▸ %s", target)))
			} else {
				sb.WriteString(styles.Normal.Render(fmt.Sprintf("    %s", target)))
			}
			sb.WriteByte('\n')
		}
		sb.WriteByte('\n')
		sb.WriteString(styles.Hint.Render("↑↓ nav  ↵ select  esc back"))

	case pingPhaseCustom:
		sb.WriteString(styles.Dim.Render("Enter target hostname or IP:"))
		sb.WriteByte('\n')
		sb.WriteString(m.input.View())
		sb.WriteByte('\n')
		sb.WriteString(styles.Hint.Render("↵ ping  esc back"))

	case pingPhaseWaiting:
		sb.WriteString(m.spinner.View())
		sb.WriteString(styles.Yellow.Render("  Pinging…"))

	case pingPhaseResult:
		sb.WriteString(m.viewResult())
	}

	return styles.AppBox.Width(40).Render(sb.String())
}

func (m pingModel) viewResult() string {
	r := m.result
	var inner strings.Builder

	if r.Success {
		inner.WriteString(styles.Green.Bold(true).Render("● PING OK") + "\n\n")
		if rtt, ok := r.Data["rtt_avg"].(float64); ok && rtt >= 0 {
			inner.WriteString(fmt.Sprintf("  RTT avg : %s\n", styles.Cyan.Render(fmt.Sprintf("%.2f ms", rtt))))
		}
		if loss, ok := r.Data["packet_loss"].(int); ok {
			col := styles.Green
			if loss > 0 {
				col = styles.Red
			}
			inner.WriteString(fmt.Sprintf("  Loss    : %s\n", col.Render(fmt.Sprintf("%d%%", loss))))
		}
		inner.WriteString(fmt.Sprintf("  Time    : %.1fs\n\n", r.Duration))
		xpBadge := styles.Badge(fmt.Sprintf("+%d XP", r.XPReward), styles.ColDarkBG, styles.ColBlue)
		inner.WriteString("  " + xpBadge)
	} else {
		inner.WriteString(styles.Red.Bold(true).Render("✗ PING FAILED") + "\n\n")
		inner.WriteString(styles.Dim.Render("  " + truncate(r.Error, 34)))
	}

	inner.WriteString("\n\n")
	inner.WriteString(styles.Hint.Render("  ↵ / esc  back to menu"))

	resultBox := styles.ResultBoxGood
	if !r.Success {
		resultBox = styles.ResultBoxBad
	}
	return resultBox.Width(36).Render(inner.String())
}

func truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n-1] + "…"
}
