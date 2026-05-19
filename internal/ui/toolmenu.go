package ui

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/d3ej/netgotchi/internal/styles"
)

type toolMenuModel struct {
	items  []string
	cursor int
	width  int
	height int
}

var toolMenuItems = []string{"PING", "SSH", "NMAP", "BACK"}

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
	var sb strings.Builder

	sb.WriteString(styles.Green.Bold(true).Render("[ TOOLS ]"))
	sb.WriteByte('\n')
	sb.WriteString(styles.Dim.Render(strings.Repeat("─", 22)))
	sb.WriteByte('\n')

	icons := map[string]string{
		"PING": "◎",
		"SSH":  "⌨",
		"NMAP": "⊕",
		"BACK": "←",
	}

	for i, item := range m.items {
		icon := icons[item]
		var line string
		if i == m.cursor {
			line = styles.Selected.Render(fmt.Sprintf("  ▸ %s %-8s", icon, item))
		} else {
			line = styles.Normal.Render(fmt.Sprintf("    %s %-8s", icon, item))
		}
		sb.WriteString(line)
		sb.WriteByte('\n')
	}

	sb.WriteByte('\n')
	sb.WriteString(styles.Hint.Render("↑↓ nav  ↵ select  esc back"))

	return styles.AppBox.Width(26).Render(sb.String())
}
