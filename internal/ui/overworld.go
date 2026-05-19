package ui

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/d3ej/netgotchi/internal/pet"
	"github.com/d3ej/netgotchi/internal/styles"
)

type overworldModel struct {
	p         *pet.Pet
	animFrame bool // toggles between idle and alternate animation
	width     int
	height    int
}

func newOverworldModel(p *pet.Pet, w, h int) overworldModel {
	return overworldModel{p: p, width: w, height: h}
}

func (m overworldModel) update(msg tea.Msg) (overworldModel, tea.Cmd) {
	switch msg := msg.(type) {
	case animTickMsg:
		m.animFrame = !m.animFrame
	case tea.KeyMsg:
		switch msg.String() {
		case " ", "enter", "s":
			return m, cmdNavigate(PageMainMenu)
		}
	}
	return m, nil
}

func (m overworldModel) view() string {
	p := m.p
	anim := "idle"
	if m.animFrame {
		switch {
		case p.Mood >= 60:
			anim = "happy"
		case p.Mood < 30:
			anim = "sad"
		default:
			anim = "wobble"
		}
	}

	sprite := pet.GetSprite(p.Stage, anim)

	var sb strings.Builder

	// Title bar
	title := styles.Title.Render("◈ NETGOTCHI ◈")
	sb.WriteString(lipgloss.PlaceHorizontal(m.width-4, lipgloss.Center, title))
	sb.WriteByte('\n')
	sb.WriteString(styles.Dim.Render(strings.Repeat("─", m.width-4)))
	sb.WriteByte('\n')

	// Pet name / stage / level line
	nameLine := fmt.Sprintf("%s  ·  %s  ·  Lv.%d",
		styles.Cyan.Render(p.Name),
		styles.Dim.Render(pet.StageTitles[p.Stage]),
		p.Level,
	)
	sb.WriteString(lipgloss.PlaceHorizontal(m.width-4, lipgloss.Center, nameLine))
	sb.WriteByte('\n')
	sb.WriteByte('\n')

	// Sprite
	for _, line := range sprite.Lines {
		colored := lipgloss.NewStyle().Foreground(spriteColor(p.Stage)).Render(line)
		sb.WriteString(lipgloss.PlaceHorizontal(m.width-4, lipgloss.Center, colored))
		sb.WriteByte('\n')
	}
	sb.WriteByte('\n')

	// Stat bars
	barW := 12
	sb.WriteString(styles.StatBar("MOOD  ", p.Mood, barW))
	sb.WriteString("  " + styles.Dim.Render(pet.MoodName(p.Mood)))
	sb.WriteByte('\n')
	sb.WriteString(styles.StatBar("HUNGER", p.Hunger, barW))
	if p.IsHungry() {
		sb.WriteString("  " + styles.Red.Render("hungry!"))
	}
	sb.WriteByte('\n')
	sb.WriteString(styles.StatBar("ENERGY", p.Energy, barW))
	if p.IsTired() {
		sb.WriteString("  " + styles.Yellow.Render("tired!"))
	}
	sb.WriteByte('\n')
	sb.WriteByte('\n')

	// XP bar
	cur, needed := p.XPToNext()
	xpPct := 0.0
	if needed > 0 {
		xpPct = float64(cur) / float64(needed) * 100
		if xpPct > 100 {
			xpPct = 100
		}
	}
	xpBar := styles.Bar(xpPct, barW, styles.XPFill, styles.BarEmpty)
	xpLine := styles.Dim.Render("XP") + " " + xpBar +
		" " + styles.Dim.Render(fmt.Sprintf("%d / %d", cur, needed))
	sb.WriteString(xpLine)
	sb.WriteByte('\n')
	sb.WriteByte('\n')

	// Footer hint
	sb.WriteString(styles.Hint.Render("[ SPACE / ENTER ]  open menu"))

	inner := sb.String()
	return styles.AppBox.Width(m.width - 2).Render(inner)
}

func spriteColor(s pet.Stage) lipgloss.Color {
	switch s {
	case pet.StageEgg:
		return lipgloss.Color("#A0E0A0")
	case pet.StageHatchling:
		return lipgloss.Color("#64DCFF")
	case pet.StageJuvenile:
		return lipgloss.Color("#FFDC00")
	case pet.StageAdult:
		return lipgloss.Color("#DC64FF")
	case pet.StageElder:
		return lipgloss.Color("#FF8C00")
	default:
		return lipgloss.Color("#FFFFFF")
	}
}
