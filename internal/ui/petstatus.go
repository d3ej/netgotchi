package ui

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
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

	sb.WriteString(styles.Magenta.Bold(true).Render("[ PET STATUS ]"))
	sb.WriteByte('\n')
	sb.WriteString(styles.Dim.Render(strings.Repeat("─", 36)))
	sb.WriteByte('\n')

	// Identity
	sb.WriteString(fmt.Sprintf("  %s  %s  Lv. %s\n",
		styles.Cyan.Render(p.Name),
		styles.Dim.Render(pet.StageTitles[p.Stage]),
		styles.Yellow.Render(fmt.Sprintf("%d", p.Level)),
	))
	sb.WriteByte('\n')

	// Stat bars
	barW := 14
	sb.WriteString(styles.StatBar("MOOD  ", p.Mood, barW))
	sb.WriteString("  " + styles.Dim.Render(pet.MoodName(p.Mood)))
	sb.WriteByte('\n')
	sb.WriteString(styles.StatBar("HUNGER", p.Hunger, barW))
	sb.WriteByte('\n')
	sb.WriteString(styles.StatBar("ENERGY", p.Energy, barW))
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
	xpBar := styles.Bar(xpPct, barW, styles.XPFill, styles.BarEmpty)
	sb.WriteString(fmt.Sprintf("  XP %s %d / %d\n",
		xpBar,
		cur, needed,
	))
	sb.WriteByte('\n')

	// Lifetime stats
	sb.WriteString(styles.Dim.Render("  Lifetime stats"))
	sb.WriteByte('\n')
	sb.WriteString(fmt.Sprintf("    Pings  : %d\n", p.TotalPings))
	sb.WriteString(fmt.Sprintf("    Scans  : %d\n", p.TotalScans))
	sb.WriteString(fmt.Sprintf("    Hosts  : %d\n", p.TotalHostsFound))
	sb.WriteByte('\n')

	// Tool affinity
	if len(p.ToolAffinity) > 0 {
		sb.WriteString(styles.Dim.Render("  Tool affinity"))
		sb.WriteByte('\n')
		for tool, count := range p.ToolAffinity {
			sb.WriteString(fmt.Sprintf("    %-8s : %d\n", tool, count))
		}
		sb.WriteByte('\n')
	}

	sb.WriteString(styles.Hint.Render("  esc / ↵  back"))

	return styles.AppBox.Width(40).Render(sb.String())
}
