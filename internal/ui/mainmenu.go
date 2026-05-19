package ui

import (
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/d3ej/netgotchi/internal/styles"
)

type mainMenuModel struct {
	items  []string
	cursor int
	width  int
	height int
}

var mainMenuItems = []string{"TOOLS", "PET", "STATUS", "EXPORT", "SAVE", "QUIT"}

var menuIcons = map[string]string{
	"TOOLS":  "⚙",
	"PET":    "♥",
	"STATUS": "◈",
	"EXPORT": "↯",
	"SAVE":   "▸",
	"QUIT":   "✕",
}

const menuBoxWidth = 28

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
	case "PET":
		return cmdNavigate(PagePetStatus)
	case "STATUS":
		return cmdNavigate(PagePetStatus)
	case "EXPORT":
		return cmdNavigate(PageExport)
	case "SAVE":
		return cmdSave()
	case "QUIT":
		return tea.Quit
	}
	return nil
}

func (m mainMenuModel) view() string {
	innerW := menuBoxWidth - 4 // border + padding

	var sb strings.Builder

	// Header bar
	header := styles.Header.Width(innerW).Align(lipgloss.Center).Render("MAIN MENU")
	sb.WriteString(header)
	sb.WriteByte('\n')
	sb.WriteString(styles.Separator(innerW))
	sb.WriteByte('\n')
	sb.WriteByte('\n')

	for i, item := range m.items {
		icon := menuIcons[item]
		label := icon + "  " + item

		var line string
		if i == m.cursor {
			line = styles.Selected.
				Width(innerW).
				Render("  " + label)
		} else {
			line = styles.Normal.
				Width(innerW).
				Render("    " + label)
		}
		sb.WriteString(line)
		sb.WriteByte('\n')
	}

	sb.WriteByte('\n')
	sb.WriteString(styles.DashedSep(innerW))
	sb.WriteByte('\n')
	sb.WriteString(styles.Hint.Render("↑↓ nav  ↵ select  esc back"))

	return styles.AppBox.Width(menuBoxWidth).Render(sb.String())
}
