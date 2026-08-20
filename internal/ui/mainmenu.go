package ui

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/d3ej/netgotchi/internal/styles"
)

type mainMenuModel struct {
	items  []string
	cursor int
	width  int
	height int
}

var mainMenuItems = []string{"TOOLS", "STATUS", "SAVE", "QUIT"}

func newMainMenuModel(w, h int) mainMenuModel {
	return mainMenuModel{items: mainMenuItems, width: w, height: h}
}

func (m mainMenuModel) update(msg tea.Msg) (mainMenuModel, tea.Cmd) {
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

func (m mainMenuModel) selectItem() tea.Cmd {
	switch m.items[m.cursor] {
	case "TOOLS":
		return cmdNavigate(PageToolMenu)
	case "STATUS":
		return cmdNavigate(PagePetStatus)
	case "SAVE":
		return cmdSave()
	case "QUIT":
		return tea.Quit
	case "PET":
		return cmdNavigate(PagePetActions)
	}
	return nil
}

func (m mainMenuModel) view() string {
	var sb strings.Builder

	sb.WriteString(styles.Header.Render("[ MAIN MENU ]"))
	sb.WriteByte('\n')
	sb.WriteString(styles.Dim.Render(strings.Repeat("─", 22)))
	sb.WriteByte('\n')

	for i, item := range m.items {
		var line string
		if i == m.cursor {
			line = styles.Selected.Render(fmt.Sprintf("  ▸ %-10s", item))
		} else {
			line = styles.Normal.Render(fmt.Sprintf("    %-10s", item))
		}
		sb.WriteString(line)
		sb.WriteByte('\n')
	}

	sb.WriteByte('\n')
	sb.WriteString(styles.Hint.Render("↑↓ nav  ↵ select  esc back"))

	return styles.AppBox.Width(26).Render(sb.String())
}
