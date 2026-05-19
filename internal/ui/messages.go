// Package ui contains all Bubbletea models (scenes) and the root AppModel.
package ui

import (
	tea "github.com/charmbracelet/bubbletea"
	"github.com/d3ej/netgotchi/internal/tools"
)

// Page identifies the active scene.
type Page int

const (
	PageOverworld Page = iota
	PageMainMenu
	PageToolMenu
	PagePing
	PageSSHAuth
	PageSSHShell
	PageScanner
	PagePetStatus
	PageExport
)

// ── Navigation messages ───────────────────────────────────────────────────

type navigateMsg struct {
	page      Page
	host      *tools.Host      // for SSHAuth
	sshParams *tools.SSHParams // for SSHShell
}

type backMsg struct{}
type saveMsg struct{}

// ── Async result messages ────────────────────────────────────────────────

type pingResultMsg struct{ result tools.ToolResult }
type scanResultMsg struct{ result tools.ToolResult }

type sshConnectedMsg struct {
	shell    *tools.SSHShell
	outputCh <-chan string
}
type sshConnectErrMsg struct{ err error }
type sshOutputMsg struct{ text string }
type sshClosedMsg struct{}

// ── Tick messages ─────────────────────────────────────────────────────────

type statTickMsg struct{}
type animTickMsg struct{}

// ── Helper commands ───────────────────────────────────────────────────────

func cmdNavigate(p Page) tea.Cmd {
	return func() tea.Msg { return navigateMsg{page: p} }
}

func cmdNavigateSSHAuth(h tools.Host) tea.Cmd {
	return func() tea.Msg { return navigateMsg{page: PageSSHAuth, host: &h} }
}

func cmdNavigateSSHShell(p tools.SSHParams) tea.Cmd {
	return func() tea.Msg { return navigateMsg{page: PageSSHShell, sshParams: &p} }
}

func cmdBack() tea.Cmd {
	return func() tea.Msg { return backMsg{} }
}

func cmdSave() tea.Cmd {
	return func() tea.Msg { return saveMsg{} }
}
