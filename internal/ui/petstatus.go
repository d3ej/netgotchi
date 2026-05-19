package ui

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/d3ej/netgotchi/internal/pet"
	"github.com/d3ej/netgotchi/internal/styles"
)

type petStatusModel struct {
	p      *pet.Pet
	width  int
	height int
}

func newPetStatusModel(p *pet.Pet, w, h int) petStatusModel {
	return petStatusModel{p: p, width: w, height: h}
}

func (m petStatusModel) update(msg tea.Msg) (petStatusModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "esc", "q", "enter":
			return m, cmdBack()
		}
	}
	return m, nil
}

func (m petStatusModel) view() string {
	p := m.p
	var sb strings.Builder
	innerW := 36

	// Header bar with magenta accent
	header := lipgloss.NewStyle().
		Background(lipgloss.Color("#1A0A2E")).
		Foreground(styles.ColMagenta).
		Bold(true).
		Width(innerW).
		Align(lipgloss.Center).
		Render("◈  PET STATUS  ◈")
	sb.WriteString(header)
	sb.WriteByte('\n')
	sb.WriteString(lipgloss.NewStyle().Foreground(styles.ColMagenta).Render(strings.Repeat("▔", innerW)))
	sb.WriteByte('\n')
	sb.WriteByte('\n')

	// Identity
	sb.WriteString(fmt.Sprintf("  %s  ·  %s  ·  Lv. %s\n",
		styles.Cyan.Render(p.Name),
		styles.Dim.Render(pet.StageTitles[p.Stage]),
		styles.Yellow.Bold(true).Render(fmt.Sprintf("%d", p.Level)),
	))
	sb.WriteByte('\n')

	// Gradient stat bars
	barW := 14
	sb.WriteString(styles.GradientStatBar("MOOD  ", p.Mood, barW))
	sb.WriteString("  " + styles.Dim.Render(pet.MoodName(p.Mood)))
	sb.WriteByte('\n')
	sb.WriteString(styles.GradientStatBar("HUNGER", p.Hunger, barW))
	if p.IsHungry() {
		sb.WriteString("  " + styles.Badge("HUNGRY", styles.ColDarkBG, styles.ColRed))
	}
	sb.WriteByte('\n')
	sb.WriteString(styles.GradientStatBar("ENERGY", p.Energy, barW))
	if p.IsTired() {
		sb.WriteString("  " + styles.Badge("TIRED", styles.ColDarkBG, styles.ColYellow))
	}
	sb.WriteByte('\n')
	sb.WriteByte('\n')

	// XP / progression
	cur, needed := p.XPToNext()
	xpPct := 0.0
	if needed > 0 {
		xpPct = float64(cur) / float64(needed) * 100
		if xpPct > 100 {
			xpPct = 100
		}
	}
	xpBar := lipgloss.NewStyle().Foreground(styles.ColBlue).Width(8).Render("XP") +
		" " + styles.GradientBar(xpPct, barW) +
		" " + styles.Dim.Render(fmt.Sprintf("%d / %d", cur, needed))
	sb.WriteString(xpBar)
	sb.WriteByte('\n')
	sb.WriteByte('\n')

	sb.WriteString(styles.DashedSep(innerW))
	sb.WriteByte('\n')

	// Lifetime stats
	sb.WriteString(styles.Dim.Render("  Lifetime stats") + "\n")
	sb.WriteString(fmt.Sprintf("    Pings  : %s\n", styles.Cyan.Render(fmt.Sprintf("%d", p.TotalPings))))
	sb.WriteString(fmt.Sprintf("    Scans  : %s\n", styles.Cyan.Render(fmt.Sprintf("%d", p.TotalScans))))
	sb.WriteString(fmt.Sprintf("    Hosts  : %s\n", styles.Cyan.Render(fmt.Sprintf("%d", p.TotalHostsFound))))
	sb.WriteByte('\n')

	// Tool affinity
	if len(p.ToolAffinity) > 0 {
		sb.WriteString(styles.Dim.Render("  Tool affinity") + "\n")
		for tool, count := range p.ToolAffinity {
			bar := styles.GradientBar(float64(count)*5, 8) // visual scale
			sb.WriteString(fmt.Sprintf("    %-8s %s %d\n", tool, bar, count))
		}
		sb.WriteByte('\n')
	}

	sb.WriteString(styles.Hint.Render("  esc / ↵  back"))

	return styles.AppBox.Width(40).Render(sb.String())
}
