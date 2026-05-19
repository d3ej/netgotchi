package ui

import (
	"fmt"
	"path/filepath"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/d3ej/netgotchi/internal/styles"
	"github.com/d3ej/netgotchi/internal/tools"
)

type exportPhase int

const (
	exportPhaseMenu    exportPhase = iota
	exportPhaseWorking
	exportPhaseDone
	exportPhaseError
)

type exportModel struct {
	session *tools.ScanSession
	cursor  int
	phase   exportPhase
	result  string
	width   int
	height  int
}

type exportDoneMsg struct {
	path string
	err  error
}

var exportLabels = []string{
	"Generic JSON",
	"Generic YAML",
	"NetBox JSON (Nautobot)",
	"Ansible YAML Inventory",
}

var exportFormats = []tools.ExportFormat{
	tools.ExportGenericJSON,
	tools.ExportGenericYAML,
	tools.ExportNetBoxJSON,
	tools.ExportAnsibleYAML,
}

func newExportModel(session *tools.ScanSession, w, h int) exportModel {
	return exportModel{session: session, width: w, height: h}
}

func (m exportModel) init() tea.Cmd { return nil }

func (m exportModel) update(msg tea.Msg) (exportModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch m.phase {
		case exportPhaseMenu:
			switch msg.String() {
			case "up", "k":
				if m.cursor > 0 {
					m.cursor--
				}
			case "down", "j":
				if m.cursor < len(exportLabels)-1 {
					m.cursor++
				}
			case "enter", " ":
				m.phase = exportPhaseWorking
				return m, m.runExport()
			case "esc", "q":
				return m, cmdBack()
			}
		case exportPhaseDone, exportPhaseError:
			return m, cmdBack()
		}

	case exportDoneMsg:
		if msg.err != nil {
			m.phase = exportPhaseError
			m.result = msg.err.Error()
		} else {
			m.phase = exportPhaseDone
			m.result = msg.path
		}
	}
	return m, nil
}

func (m exportModel) runExport() tea.Cmd {
	format := exportFormats[m.cursor]
	session := m.session
	return func() tea.Msg {
		path, err := tools.Export(session, format, "exports")
		return exportDoneMsg{path: path, err: err}
	}
}

func (m exportModel) view() string {
	var sb strings.Builder

	sb.WriteString(styles.Header.Render("[ EXPORT INVENTORY ]"))
	sb.WriteByte('\n')
	sb.WriteString(styles.Dim.Render(strings.Repeat("─", 30)))
	sb.WriteByte('\n')

	switch m.phase {
	case exportPhaseMenu:
		count := 0
		if m.session != nil {
			count = m.session.HostCount()
		}
		sb.WriteString(styles.Dim.Render(fmt.Sprintf("  %d host(s) discovered this session\n\n", count)))

		for i, label := range exportLabels {
			if i == m.cursor {
				sb.WriteString(styles.Selected.Render(fmt.Sprintf("  ▸ %-26s", label)))
			} else {
				sb.WriteString(styles.Normal.Render(fmt.Sprintf("    %-26s", label)))
			}
			sb.WriteByte('\n')
		}

		sb.WriteByte('\n')
		sb.WriteString(styles.Hint.Render("↑↓ nav  ↵ export  esc back"))

	case exportPhaseWorking:
		sb.WriteString(styles.Cyan.Render("\n  ◌ Writing export file...\n"))

	case exportPhaseDone:
		sb.WriteString(styles.Green.Render("\n  ✓ Export complete!\n\n"))
		sb.WriteString(styles.Dim.Render("  File: ") + styles.Normal.Render(filepath.Base(m.result)) + "\n")
		sb.WriteString(styles.Dim.Render("  Path: ") + styles.Normal.Render(m.result) + "\n")
		sb.WriteString(styles.Dim.Render("\n  Permissions: 0600 (owner only)\n"))
		sb.WriteString(styles.Hint.Render("\n  Press any key to go back"))

	case exportPhaseError:
		sb.WriteString(styles.Red.Render("\n  ✗ Export failed\n\n"))
		sb.WriteString(styles.Dim.Render("  ") + styles.Normal.Render(m.result) + "\n")
		sb.WriteString(styles.Hint.Render("\n  Press any key to go back"))
	}

	return styles.AppBox.Width(36).Render(sb.String())
}
