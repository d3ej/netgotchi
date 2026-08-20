package ui

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/textinput"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/d3ej/netgotchi/internal/pet"
	"github.com/d3ej/netgotchi/internal/styles"
	"github.com/d3ej/netgotchi/internal/tools"
)

type shellPhase int

const (
	shellPhaseConnecting shellPhase = iota
	shellPhaseActive
	shellPhaseClosed
	shellPhaseError
)

type sshShellModel struct {
	p        *pet.Pet
	params   tools.SSHParams
	shell    *tools.SSHShell
	outputCh <-chan string
	phase    shellPhase
	errMsg   string

	viewport viewport.Model
	input    textinput.Model
	spinner  spinner.Model

	lines  []string // raw accumulated output lines
	width  int
	height int
}

func newSSHShellModel(p *pet.Pet, params tools.SSHParams, w, h int) sshShellModel {
	vpH := h - 10
	if vpH < 4 {
		vpH = 4
	}
	vp := viewport.New(w-6, vpH)
	vp.SetContent("")

	ti := textinput.New()
	ti.Placeholder = "command…"
	ti.CharLimit = 512
	ti.Width = w - 8
	ti.Prompt = "$ "

	s := spinner.New()
	s.Spinner = spinner.Dot
	s.Style = lipgloss.NewStyle().Foreground(styles.ColGreen)

	return sshShellModel{
		p:        p,
		params:   params,
		phase:    shellPhaseConnecting,
		viewport: vp,
		input:    ti,
		spinner:  s,
		width:    w,
		height:   h,
	}
}

func (m sshShellModel) init() tea.Cmd {
	return tea.Batch(m.spinner.Tick, connectSSHCmd(m.params))
}

func connectSSHCmd(params tools.SSHParams) tea.Cmd {
	return func() tea.Msg {
		sh, ch, err := tools.OpenSSHShell(params)
		if err != nil {
			return sshConnectErrMsg{err: err}
		}
		return sshConnectedMsg{shell: sh, outputCh: ch}
	}
}

func waitForSSHOutput(ch <-chan string) tea.Cmd {
	return func() tea.Msg {
		text, ok := <-ch
		if !ok {
			return sshClosedMsg{}
		}
		return sshOutputMsg{text: text}
	}
}

func (m sshShellModel) update(msg tea.Msg) (sshShellModel, tea.Cmd) {
	switch msg := msg.(type) {
	case sshConnectedMsg:
		m.shell = msg.shell
		m.outputCh = msg.outputCh
		m.phase = shellPhaseActive
		m.input.Focus()
		m.appendOutput(fmt.Sprintf("*** Connected to %s ***\n", m.params.Host))
		m.p.EarnXP(20, "ssh")
		return m, tea.Batch(textinput.Blink, waitForSSHOutput(m.outputCh))

	case sshConnectErrMsg:
		m.phase = shellPhaseError
		m.errMsg = msg.err.Error()
		return m, nil

	case sshOutputMsg:
		m.appendOutput(msg.text)
		return m, waitForSSHOutput(m.outputCh)

	case sshClosedMsg:
		m.phase = shellPhaseClosed
		m.appendOutput("\n*** Session closed ***\n")
		return m, nil

	case tea.KeyMsg:
		if m.phase != shellPhaseActive {
			if msg.String() == "esc" || msg.String() == "q" {
				if m.shell != nil {
					m.shell.Close()
				}
				return m, cmdBack()
			}
			return m, nil
		}

		switch msg.String() {
		case "ctrl+c", "esc":
			if m.shell != nil {
				m.shell.Close()
			}
			return m, cmdBack()

		case "enter":
			line := strings.TrimSpace(m.input.Value())
			if line != "" && m.shell != nil {
				m.appendOutput("$ " + line + "\n")
				_ = m.shell.Send(line + "\n")
				m.input.SetValue("")
				m.viewport.GotoBottom()
			}
			return m, nil

		case "pgup":
			m.viewport.HalfViewUp()
			return m, nil

		case "pgdown":
			m.viewport.HalfViewDown()
			return m, nil
		}

		// Forward to text input
		var tiCmd tea.Cmd
		m.input, tiCmd = m.input.Update(msg)
		return m, tiCmd
	}

	// Spinner update while connecting
	if m.phase == shellPhaseConnecting {
		var cmd tea.Cmd
		m.spinner, cmd = m.spinner.Update(msg)
		return m, cmd
	}

	// Viewport passthrough
	var vpCmd tea.Cmd
	m.viewport, vpCmd = m.viewport.Update(msg)
	return m, vpCmd
}

func (m *sshShellModel) appendOutput(text string) {
	m.lines = append(m.lines, text)
	if len(m.lines) > 500 {
		m.lines = m.lines[len(m.lines)-500:]
	}
	content := strings.Join(m.lines, "")
	m.viewport.SetContent(content)
	m.viewport.GotoBottom()
}

func (m sshShellModel) view() string {
	var sb strings.Builder

	host := m.params.Host
	sb.WriteString(styles.Green.Bold(true).Render(fmt.Sprintf("[ SSH  %s ]", host)))
	sb.WriteByte('\n')
	sb.WriteString(styles.Dim.Render(strings.Repeat("─", m.width-4)))
	sb.WriteByte('\n')

	switch m.phase {
	case shellPhaseConnecting:
		sb.WriteString(m.spinner.View())
		sb.WriteString(styles.Yellow.Render(fmt.Sprintf("  Connecting to %s…", host)))

	case shellPhaseActive:
		sb.WriteString(styles.Terminal.Render(m.viewport.View()))
		sb.WriteByte('\n')
		sb.WriteString(styles.Dim.Render(strings.Repeat("─", m.width-4)))
		sb.WriteByte('\n')
		sb.WriteString(m.input.View())
		sb.WriteByte('\n')
		sb.WriteString(styles.Hint.Render("↵ send  pgup/dn scroll  esc disconnect"))

	case shellPhaseClosed:
		sb.WriteString(styles.Terminal.Render(m.viewport.View()))
		sb.WriteByte('\n')
		sb.WriteString(styles.Yellow.Render("Session ended."))
		sb.WriteByte('\n')
		sb.WriteString(styles.Hint.Render("esc / q  back"))

	case shellPhaseError:
		sb.WriteString(styles.Red.Render("✗ Connection failed"))
		sb.WriteByte('\n')
		sb.WriteString(styles.Dim.Render(truncate(m.errMsg, m.width-6)))
		sb.WriteByte('\n')
		sb.WriteString(styles.Hint.Render("esc / q  back"))
	}

	return styles.AppBox.Width(m.width - 2).Render(sb.String())
}
