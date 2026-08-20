package ui

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/d3ej/netgotchi/internal/styles"
)

type petMenuModel struct {
	items  []string
	cursor int
	width  int
	height int
}

var petMenuItems = []string{"FEED", "EXERCISE", "TEACH", "BACK"}

func newpetMenuModel(w, h int) petMenuModel {
	return petMenuModel{items: petMenuItems, width: w, height: h}
}

func (m petMenuModel) update(msg tea.Msg) (petMenuModel, tea.Cmd) {
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

func (m petMenuModel) selectItem() tea.Cmd {
	switch m.items[m.cursor] {
	case "FEED":
		return cmdNavigate(PagePing)
	case "EXERCISE":
		return cmdNavigate(PageSSHAuth)
	case "TEACH":
		return cmdNavigate(PageScanner)
	case "BACK":
		return cmdBack()
	}
	return nil
}

func (m petMenuModel) view() string {
	var sb strings.Builder

	sb.WriteString(styles.Green.Bold(true).Render("[ ACTIONS ]"))
	sb.WriteByte('\n')
	sb.WriteString(styles.Dim.Render(strings.Repeat("-", 22)))
	sb.WriteByte('\n')

	icons := map[string]string{
		"FEED":     "🍏",
		"EXERCISE": "🏃",
		"TEACH":    "🕮",
		"BACK":     "←",
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
