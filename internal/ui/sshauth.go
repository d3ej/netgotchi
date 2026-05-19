package ui

import (
	"fmt"
	"os"
	"strings"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/d3ej/netgotchi/internal/styles"
	"github.com/d3ej/netgotchi/internal/tools"
)

type sshAuthPhase int

const (
	sshAuthPhaseHostPick sshAuthPhase = iota
	sshAuthPhaseMethod
	sshAuthPhaseFields
)

var authMethods = []string{"Password", "Key File", "Agent / Auto"}
var authMethodKeys = []string{"password", "key", "agent"}

type sshAuthModel struct {
	hosts       []tools.Host
	hostCursor  int
	methodCursor int
	phase       sshAuthPhase
	selectedHost *tools.Host
	inputs      []textinput.Model // [username, secret]
	focusIdx    int
	width       int
	height      int
}

func newSSHAuthModel(w, h int) sshAuthModel {
	hosts := tools.DiscoverHosts()
	m := sshAuthModel{
		hosts:  hosts,
		width:  w,
		height: h,
		phase:  sshAuthPhaseHostPick,
	}
	return m
}

// withHost pre-selects a host (used when navigating directly to auth from a
// host that was already selected elsewhere).
func (m sshAuthModel) withHost(h tools.Host) sshAuthModel {
	m.selectedHost = &h
	m.phase = sshAuthPhaseMethod
	return m
}

func (m sshAuthModel) init() tea.Cmd { return nil }

func (m sshAuthModel) update(msg tea.Msg) (sshAuthModel, tea.Cmd) {
	switch m.phase {
	case sshAuthPhaseHostPick:
		return m.updateHostPick(msg)
	case sshAuthPhaseMethod:
		return m.updateMethod(msg)
	case sshAuthPhaseFields:
		return m.updateFields(msg)
	}
	return m, nil
}

func (m sshAuthModel) updateHostPick(msg tea.Msg) (sshAuthModel, tea.Cmd) {
	items := append([]string{}, hostLabels(m.hosts)...)
	items = append(items, "CUSTOM", "BACK")

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.hostCursor > 0 {
				m.hostCursor--
			}
		case "down", "j":
			if m.hostCursor < len(items)-1 {
				m.hostCursor++
			}
		case "enter", " ":
			if m.hostCursor < len(m.hosts) {
				h := m.hosts[m.hostCursor]
				m.selectedHost = &h
				m.phase = sshAuthPhaseMethod
			} else if items[m.hostCursor] == "CUSTOM" {
				// Build a placeholder host; user will fill in via a text input
				// We reuse the first "fields" slot for the custom hostname.
				h := tools.Host{Name: "custom", Addr: "", Port: 22}
				m.selectedHost = &h
				m.phase = sshAuthPhaseMethod
			} else {
				return m, cmdBack()
			}
		case "esc", "q":
			return m, cmdBack()
		}
	}
	return m, nil
}

func (m sshAuthModel) updateMethod(msg tea.Msg) (sshAuthModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.methodCursor > 0 {
				m.methodCursor--
			}
		case "down", "j":
			if m.methodCursor < len(authMethods)-1 {
				m.methodCursor++
			}
		case "enter", " ":
			m.phase = sshAuthPhaseFields
			m.inputs = buildInputs(authMethodKeys[m.methodCursor], m.selectedHost)
			m.focusIdx = 0
			m.inputs[0].Focus()
			return m, textinput.Blink
		case "esc":
			m.phase = sshAuthPhaseHostPick
		}
	}
	return m, nil
}

func (m sshAuthModel) updateFields(msg tea.Msg) (sshAuthModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "tab", "down":
			m.inputs[m.focusIdx].Blur()
			m.focusIdx = (m.focusIdx + 1) % len(m.inputs)
			m.inputs[m.focusIdx].Focus()
			return m, textinput.Blink
		case "shift+tab", "up":
			m.inputs[m.focusIdx].Blur()
			m.focusIdx = (m.focusIdx - 1 + len(m.inputs)) % len(m.inputs)
			m.inputs[m.focusIdx].Focus()
			return m, textinput.Blink
		case "enter":
			if m.focusIdx < len(m.inputs)-1 {
				m.inputs[m.focusIdx].Blur()
				m.focusIdx++
				m.inputs[m.focusIdx].Focus()
				return m, textinput.Blink
			}
			// Last field → submit
			return m, m.submit()
		case "esc":
			m.phase = sshAuthPhaseMethod
			for i := range m.inputs {
				m.inputs[i].Blur()
			}
			return m, nil
		}
	}

	// Forward to focused input
	var cmd tea.Cmd
	m.inputs[m.focusIdx], cmd = m.inputs[m.focusIdx].Update(msg)
	return m, cmd
}

func (m sshAuthModel) submit() tea.Cmd {
	method := authMethodKeys[m.methodCursor]
	host := m.selectedHost

	// If custom host, first input is the address
	if host.Addr == "" && len(m.inputs) > 0 {
		host.Addr = strings.TrimSpace(m.inputs[0].Value())
		host.Name = host.Addr
	}

	params := tools.SSHParams{
		Host:       host.Addr,
		Port:       host.Port,
		AuthMethod: method,
	}
	if params.Port == 0 {
		params.Port = 22
	}

	switch method {
	case "password":
		params.Username = strings.TrimSpace(m.inputs[0].Value())
		params.Password = m.inputs[1].Value()
	case "key":
		params.Username = strings.TrimSpace(m.inputs[0].Value())
		params.KeyPath = strings.TrimSpace(m.inputs[1].Value())
	case "agent":
		params.Username = strings.TrimSpace(m.inputs[0].Value())
	}

	return cmdNavigateSSHShell(params)
}

func (m sshAuthModel) view() string {
	var sb strings.Builder
	innerW := 38

	header := styles.ToolHeader.Width(innerW).Align(lipgloss.Center).Render("SSH AUTH")
	sb.WriteString(header)
	sb.WriteByte('\n')
	sb.WriteString(styles.Separator(innerW))
	sb.WriteByte('\n')

	switch m.phase {
	case sshAuthPhaseHostPick:
		sb.WriteString(styles.Dim.Render("Select host:"))
		sb.WriteByte('\n')
		items := append(hostLabels(m.hosts), "CUSTOM", "BACK")
		for i, item := range items {
			if i == m.hostCursor {
				sb.WriteString(styles.Selected.Render(fmt.Sprintf("  ▸ %s", item)))
			} else {
				sb.WriteString(styles.Normal.Render(fmt.Sprintf("    %s", item)))
			}
			sb.WriteByte('\n')
		}
		sb.WriteString(styles.Hint.Render("↑↓ nav  ↵ select  esc back"))

	case sshAuthPhaseMethod:
		hostName := ""
		if m.selectedHost != nil {
			hostName = m.selectedHost.Name
		}
		sb.WriteString(styles.Cyan.Render(fmt.Sprintf("Host: %s", hostName)))
		sb.WriteByte('\n')
		sb.WriteString(styles.Dim.Render("Auth method:"))
		sb.WriteByte('\n')
		for i, method := range authMethods {
			if i == m.methodCursor {
				sb.WriteString(styles.Selected.Render(fmt.Sprintf("  ▸ %s", method)))
			} else {
				sb.WriteString(styles.Normal.Render(fmt.Sprintf("    %s", method)))
			}
			sb.WriteByte('\n')
		}
		sb.WriteString(styles.Hint.Render("↑↓ nav  ↵ select  esc back"))

	case sshAuthPhaseFields:
		method := authMethods[m.methodCursor]
		sb.WriteString(styles.Cyan.Render(fmt.Sprintf("Method: %s", method)))
		sb.WriteByte('\n')
		sb.WriteString(styles.Dim.Render("Fill in credentials:"))
		sb.WriteByte('\n')
		for _, ti := range m.inputs {
			sb.WriteString(ti.View())
			sb.WriteByte('\n')
		}
		sb.WriteByte('\n')
		sb.WriteString(styles.Hint.Render("tab/↑↓ switch  ↵ next/connect  esc back"))
	}

	return styles.AppBox.Width(44).Render(sb.String())
}

func hostLabels(hosts []tools.Host) []string {
	labels := make([]string, len(hosts))
	for i, h := range hosts {
		if h.User != "" {
			labels[i] = fmt.Sprintf("%s (%s@%s)", h.Name, h.User, h.Addr)
		} else {
			labels[i] = fmt.Sprintf("%s (%s)", h.Name, h.Addr)
		}
	}
	return labels
}

func buildInputs(method string, host *tools.Host) []textinput.Model {
	defaultUser := ""
	if host != nil && host.User != "" {
		defaultUser = host.User
	} else {
		defaultUser = os.Getenv("USER")
	}

	username := textinput.New()
	username.Placeholder = "username"
	username.SetValue(defaultUser)
	username.CharLimit = 64
	username.Width = 30
	username.Prompt = "  Username : "

	switch method {
	case "password":
		pw := textinput.New()
		pw.Placeholder = "password"
		pw.EchoMode = textinput.EchoPassword
		pw.EchoCharacter = '●'
		pw.CharLimit = 128
		pw.Width = 30
		pw.Prompt = "  Password : "
		return []textinput.Model{username, pw}

	case "key":
		home, _ := os.UserHomeDir()
		kp := textinput.New()
		kp.Placeholder = "~/.ssh/id_rsa"
		kp.SetValue(home + "/.ssh/id_rsa")
		kp.CharLimit = 256
		kp.Width = 30
		kp.Prompt = "  Key path : "
		return []textinput.Model{username, kp}

	default: // agent
		return []textinput.Model{username}
	}
}
