// Package styles defines the shared Lip Gloss color palette and reusable
// styles for every scene.  The palette mirrors the GBC-inspired colors from
// the original pygame version.
package styles

import (
	"fmt"

	"github.com/charmbracelet/lipgloss"
)

// Palette – base colors
const (
	ColDarkBG  = lipgloss.Color("#08080F")
	ColWhite   = lipgloss.Color("#E8E8F0")
	ColGray    = lipgloss.Color("#8C8CA0")
	ColCyan    = lipgloss.Color("#64DCFF")
	ColGreen   = lipgloss.Color("#32FF32")
	ColRed     = lipgloss.Color("#FF5050")
	ColYellow  = lipgloss.Color("#FFDC00")
	ColBlue    = lipgloss.Color("#6464FF")
	ColMagenta = lipgloss.Color("#DC64FF")

	// Bars
	ColBarFill  = lipgloss.Color("#32A032")
	ColBarEmpty = lipgloss.Color("#1E1E2E")
	ColXPFill   = lipgloss.Color("#3264FF")
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

	// Structural
	Header = lipgloss.NewStyle().
		Foreground(ColCyan).
		Bold(true).
		Padding(0, 1)

	Title = lipgloss.NewStyle().
		Foreground(ColGreen).
		Bold(true)

	Selected = lipgloss.NewStyle().
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

	// SSH terminal text
	Terminal = lipgloss.NewStyle().
			Foreground(ColGreen)

	// Status bar fill and empty blocks
	BarFill  = lipgloss.NewStyle().Foreground(ColBarFill).Render("█")
	BarEmpty = lipgloss.NewStyle().Foreground(ColBarEmpty).Render("░")
	XPFill   = lipgloss.NewStyle().Foreground(ColXPFill).Render("█")
)

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

// StatBar renders a labeled stat bar like "HUNGER ▓▓▓▓░░ 64%".
func StatBar(label string, pct float64, barWidth int) string {
	bar := Bar(pct, barWidth, BarFill, BarEmpty)
	pctStr := lipgloss.NewStyle().Foreground(ColGray).Render(fmt.Sprintf("%3.0f%%", pct))
	lbl := lipgloss.NewStyle().Foreground(ColWhite).Width(8).Render(label)
	return lbl + " " + bar + " " + pctStr
}
