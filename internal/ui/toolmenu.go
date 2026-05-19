package ui

import (
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/d3ej/netgotchi/internal/styles"
)

type toolMenuModel struct {
	items  []string
	cursor int
	width  int
	height int
}

var toolMenuItems = []string{"PING", "SSH", "NMAP", "BACK"}

var toolIcons = map[string]string{
	"PING": "◎",
	"SSH":  "⌨",
	"NMAP": "⊕",
	"BACK": "←",
}

const toolBoxWidth = 26

func newToolMenuModel(w, h int) toolMenuModel {
	return toolMenuModel{items: toolMenuItems, width: w, height: h}
}

func (m toolMenuModel) update(msg tea.Msg) (toolMenuModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.items)-1 {
				m.cursor++
			}
		case "enter", " ":
			return m, m.selectItem()
		case "esc", "q":
			return m, cmdBack()
		}
	}
	return m, nil
}

func (m toolMenuModel) selectItem() tea.Cmd {
	switch m.items[m.cursor] {
	case "PING":
		return cmdNavigate(PagePing)
	case "SSH":
		return cmdNavigate(PageSSHAuth)
	case "NMAP":
		return cmdNavigate(PageScanner)
	case "BACK":
		return cmdBack()
	}
	return nil
}

func (m toolMenuModel) view() string {
	innerW := toolBoxWidth - 4

	var sb strings.Builder

	header := styles.ToolHeader.Width(innerW).Align(lipgloss.Center).Render("NETWORK TOOLS")
	sb.WriteString(header)
	sb.WriteByte('\n')
	sb.WriteString(styles.Separator(innerW))
	sb.WriteByte('\n')
	sb.WriteByte('\n')

	for i, item := range m.items {
		icon := toolIcons[item]
		label := icon + "  " + item
		var line string
		if i == m.cursor {
			line = styles.Selected.Width(innerW).Render("  " + label)
		} else {
			line = styles.Normal.Width(innerW).Render("    " + label)
		}
		sb.WriteString(line)
		sb.WriteByte('\n')
	}

	sb.WriteByte('\n')
	sb.WriteString(styles.DashedSep(innerW))
	sb.WriteByte('\n')
	sb.WriteString(styles.Hint.Render("↑↓ nav  ↵ select  esc back"))

	return styles.AppBox.Width(toolBoxWidth).Render(sb.String())
}
