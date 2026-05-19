// Package styles defines the shared Lip Gloss color palette and reusable
// styles for every scene.  The palette mirrors the GBC-inspired colors from
// the original pygame version.
package styles

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
)

// Palette – base colors
const (
	ColDarkBG   = lipgloss.Color("#08080F")
	ColDarkPanel = lipgloss.Color("#0D0D1F")
	ColWhite    = lipgloss.Color("#E8E8F0")
	ColGray     = lipgloss.Color("#8C8CA0")
	ColCyan     = lipgloss.Color("#64DCFF")
	ColGreen    = lipgloss.Color("#32FF32")
	ColRed      = lipgloss.Color("#FF5050")
	ColYellow   = lipgloss.Color("#FFDC00")
	ColBlue     = lipgloss.Color("#6464FF")
	ColMagenta  = lipgloss.Color("#DC64FF")
	ColOrange   = lipgloss.Color("#FF8C00")

	// Bars
	ColBarFill    = lipgloss.Color("#32A032")
	ColBarMid     = lipgloss.Color("#A0A000")
	ColBarLow     = lipgloss.Color("#A03030")
	ColBarEmpty   = lipgloss.Color("#1E1E2E")
	ColXPFill     = lipgloss.Color("#3264FF")

	// Header backgrounds
	ColHeaderBG     = lipgloss.Color("#0A0A28")
	ColToolHeaderBG = lipgloss.Color("#082008")
)

// Base styles
var (
	Base = lipgloss.NewStyle().
		Background(ColDarkBG).
		Foreground(ColWhite)

	Bold = Base.Bold(true)

	Dim = Base.Foreground(ColGray)

	// Text accent styles
	Cyan    = Base.Foreground(ColCyan)
	Green   = Base.Foreground(ColGreen)
	Red     = Base.Foreground(ColRed)
	Yellow  = Base.Foreground(ColYellow)
	Blue    = Base.Foreground(ColBlue)
	Magenta = Base.Foreground(ColMagenta)

	// Header: solid dark-blue background, cyan bold text, full-width feel
	Header = lipgloss.NewStyle().
		Background(ColHeaderBG).
		Foreground(ColCyan).
		Bold(true).
		Padding(0, 1)

	// ToolHeader: dark green bg for tool scenes
	ToolHeader = lipgloss.NewStyle().
		Background(ColToolHeaderBG).
		Foreground(ColGreen).
		Bold(true).
		Padding(0, 1)

	Title = lipgloss.NewStyle().
		Foreground(ColGreen).
		Bold(true)

	Selected = lipgloss.NewStyle().
		Background(lipgloss.Color("#1A1A3F")).
		Foreground(ColYellow).
		Bold(true)

	Normal = lipgloss.NewStyle().
		Foreground(ColWhite)

	Hint = lipgloss.NewStyle().
		Foreground(ColGray)

	// App container – rounded border, dark background
	AppBox = lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(ColCyan).
		Padding(0, 1)

	// Inner panel (no border, just spacing)
	Panel = lipgloss.NewStyle().
		Padding(0, 1)

	// Dialog / result box
	ResultBox = lipgloss.NewStyle().
		Border(lipgloss.NormalBorder()).
		BorderForeground(ColGray).
		Padding(0, 1)

	ResultBoxGood = lipgloss.NewStyle().
		Border(lipgloss.NormalBorder()).
		BorderForeground(ColGreen).
		Padding(0, 1)

	ResultBoxBad = lipgloss.NewStyle().
		Border(lipgloss.NormalBorder()).
		BorderForeground(ColRed).
		Padding(0, 1)

	// SSH terminal text
	Terminal = lipgloss.NewStyle().
		Foreground(ColGreen)

	// Status bar fill and empty blocks
	BarFill  = lipgloss.NewStyle().Foreground(ColBarFill).Render("█")
	BarEmpty = lipgloss.NewStyle().Foreground(ColBarEmpty).Render("░")
	XPFill   = lipgloss.NewStyle().Foreground(ColXPFill).Render("█")
)

// gradient block chars from thin to full
var gradientBlocks = []string{"▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"}

// Bar renders a percentage bar of the given width.
// pct must be in [0, 100].
func Bar(pct float64, width int, fill, empty string) string {
	if width <= 0 {
		width = 10
	}
	filled := int(pct / 100.0 * float64(width))
	if filled > width {
		filled = width
	}
	out := ""
	for i := 0; i < filled; i++ {
		out += fill
	}
	for i := filled; i < width; i++ {
		out += empty
	}
	return out
}

// GradientBar renders a smooth percentage bar using Unicode block characters.
// The fill color shifts from green → yellow → red as pct drops below thresholds.
func GradientBar(pct float64, width int) string {
	if width <= 0 {
		width = 10
	}
	fillColor := barColor(pct)
	emptyStyle := lipgloss.NewStyle().Foreground(ColBarEmpty)
	fillStyle := lipgloss.NewStyle().Foreground(fillColor)

	filled := int(pct / 100.0 * float64(width))
	if filled > width {
		filled = width
	}

	// Fractional sub-block for smoother look
	fracIdx := -1
	if filled < width {
		frac := (pct/100.0*float64(width)) - float64(filled)
		if frac > 0.1 {
			fracIdx = int(frac * float64(len(gradientBlocks)))
			if fracIdx >= len(gradientBlocks) {
				fracIdx = len(gradientBlocks) - 1
			}
		}
	}

	var sb strings.Builder
	for i := 0; i < filled; i++ {
		sb.WriteString(fillStyle.Render("█"))
	}
	if fracIdx >= 0 && filled < width {
		sb.WriteString(fillStyle.Render(gradientBlocks[fracIdx]))
		for i := filled + 1; i < width; i++ {
			sb.WriteString(emptyStyle.Render("░"))
		}
	} else {
		for i := filled; i < width; i++ {
			sb.WriteString(emptyStyle.Render("░"))
		}
	}
	return sb.String()
}

func barColor(pct float64) lipgloss.Color {
	switch {
	case pct > 55:
		return ColBarFill
	case pct > 25:
		return ColBarMid
	default:
		return ColBarLow
	}
}

// StatBar renders a labeled stat bar like "HUNGER ▓▓▓▓░░ 64%".
func StatBar(label string, pct float64, barWidth int) string {
	bar := Bar(pct, barWidth, BarFill, BarEmpty)
	pctStr := lipgloss.NewStyle().Foreground(ColGray).Render(fmt.Sprintf("%3.0f%%", pct))
	lbl := lipgloss.NewStyle().Foreground(ColWhite).Width(8).Render(label)
	return lbl + " " + bar + " " + pctStr
}

// GradientStatBar renders a labeled stat bar with color-coded gradient fill.
func GradientStatBar(label string, pct float64, barWidth int) string {
	bar := GradientBar(pct, barWidth)
	col := lipgloss.NewStyle().Foreground(barColor(pct))
	pctStr := col.Render(fmt.Sprintf("%3.0f%%", pct))
	lbl := lipgloss.NewStyle().Foreground(ColWhite).Width(8).Render(label)
	return lbl + " " + bar + " " + pctStr
}

// Badge renders a small highlighted label pill.
func Badge(text string, fg, bg lipgloss.Color) string {
	return lipgloss.NewStyle().
		Background(bg).
		Foreground(fg).
		Padding(0, 1).
		Bold(true).
		Render(text)
}

// Separator renders a horizontal rule string of given width.
func Separator(width int) string {
	return Dim.Render(strings.Repeat("─", width))
}

// DashedSep renders a dashed separator.
func DashedSep(width int) string {
	return Dim.Render(strings.Repeat("╌", width))
}
