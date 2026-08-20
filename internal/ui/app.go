package ui

import (
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/d3ej/netgotchi/internal/pet"
	"github.com/d3ej/netgotchi/internal/save"
	"github.com/d3ej/netgotchi/internal/styles"
)

// AppModel is the root Bubbletea model.  It owns the navigation stack and
// delegates update/view calls to whichever scene is on top.
type AppModel struct {
	p       *pet.Pet
	page    Page
	history []Page
	width   int
	height  int

	// Sub-models — only the active one is rendered
	overworld overworldModel
	mainMenu  mainMenuModel
	toolMenu  toolMenuModel
	ping      pingModel
	sshAuth   sshAuthModel
	sshShell  sshShellModel
	scanner   scannerModel
	petStatus petStatusModel

	statusMsg string // transient notification (e.g. "Saved!")
	statusTTL float64
}

// New loads the save file (or creates a fresh pet) and returns an AppModel
// ready to hand to tea.NewProgram.
func New() (AppModel, error) {
	p := save.Load("")
	// Apply any offline decay since last session
	elapsed := time.Since(p.LastUpdate).Seconds()
	if elapsed > 0 {
		p.Update(elapsed)
	}

	m := AppModel{
		p:    p,
		page: PageOverworld,
	}
	// All sub-models are initialised lazily when navigated to, except the
	// first scene which must be ready immediately.
	m.overworld = newOverworldModel(p, 80, 24)
	return m, nil
}

func (m AppModel) Init() tea.Cmd {
	return tea.Batch(
		statTickCmd(),
		animTickCmd(),
	)
}

func statTickCmd() tea.Cmd {
	return tea.Tick(5*time.Second, func(time.Time) tea.Msg { return statTickMsg{} })
}

const animTickInterval = 600 * time.Millisecond

func animTickCmd() tea.Cmd {
	return tea.Tick(animTickInterval, func(time.Time) tea.Msg { return animTickMsg{} })
}

func (m AppModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {

	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height
		m.overworld.width, m.overworld.height = m.width, m.height
		m.sshShell.width, m.sshShell.height = m.width, m.height
		return m, nil

	case tea.KeyMsg:
		if msg.String() == "ctrl+c" {
			return m, tea.Quit
		}

	case statTickMsg:
		m.p.Update(5)
		return m, statTickCmd()

	case animTickMsg:
		if m.statusMsg != "" {
			m.statusTTL -= animTickInterval.Seconds()
			if m.statusTTL <= 0 {
				m.statusMsg = ""
			}
		}
		var owCmd tea.Cmd
		m.overworld, owCmd = m.overworld.update(msg)
		return m, tea.Batch(owCmd, animTickCmd())

	case navigateMsg:
		return m.handleNavigate(msg)

	case backMsg:
		return m.handleBack()

	case saveMsg:
		if err := save.Save(m.p, ""); err == nil {
			m.statusMsg = "Game saved!"
		} else {
			m.statusMsg = "Save failed: " + err.Error()
		}
		m.statusTTL = 3
		return m, nil
	}

	// Delegate to the active scene
	return m.delegateUpdate(msg)
}

func (m AppModel) handleNavigate(msg navigateMsg) (AppModel, tea.Cmd) {
	m.history = append(m.history, m.page)
	m.page = msg.page

	switch msg.page {
	case PageMainMenu:
		m.mainMenu = newMainMenuModel(m.width, m.height)
	case PageToolMenu:
		m.toolMenu = newToolMenuModel(m.width, m.height)
	case PagePing:
		m.ping = newPingModel(m.p, m.width, m.height)
		return m, m.ping.init()
	case PageSSHAuth:
		m.sshAuth = newSSHAuthModel(m.width, m.height)
		if msg.host != nil {
			m.sshAuth = m.sshAuth.withHost(*msg.host)
		}
		return m, m.sshAuth.init()
	case PageSSHShell:
		if msg.sshParams == nil {
			return m.handleBack()
		}
		m.sshShell = newSSHShellModel(m.p, *msg.sshParams, m.width, m.height)
		return m, m.sshShell.init()
	case PageScanner:
		m.scanner = newScannerModel(m.p, m.width, m.height)
		return m, m.scanner.init()
	case PagePetStatus:
		m.petStatus = newPetStatusModel(m.p, m.width, m.height)
	}
	return m, nil
}

func (m AppModel) handleBack() (AppModel, tea.Cmd) {
	if len(m.history) == 0 {
		return m, nil
	}
	m.page = m.history[len(m.history)-1]
	m.history = m.history[:len(m.history)-1]
	return m, nil
}

func (m AppModel) delegateUpdate(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd
	switch m.page {
	case PageOverworld:
		m.overworld, cmd = m.overworld.update(msg)
	case PageMainMenu:
		m.mainMenu, cmd = m.mainMenu.update(msg)
	case PageToolMenu:
		m.toolMenu, cmd = m.toolMenu.update(msg)
	case PagePing:
		m.ping, cmd = m.ping.update(msg)
	case PageSSHAuth:
		m.sshAuth, cmd = m.sshAuth.update(msg)
	case PageSSHShell:
		m.sshShell, cmd = m.sshShell.update(msg)
	case PageScanner:
		m.scanner, cmd = m.scanner.update(msg)
	case PagePetStatus:
		m.petStatus, cmd = m.petStatus.update(msg)
	}
	return m, cmd
}

func (m AppModel) View() string {
	var scene string
	switch m.page {
	case PageOverworld:
		scene = m.overworld.view()
	case PageMainMenu:
		scene = m.mainMenu.view()
	case PageToolMenu:
		scene = m.toolMenu.view()
	case PagePing:
		scene = m.ping.view()
	case PageSSHAuth:
		scene = m.sshAuth.view()
	case PageSSHShell:
		scene = m.sshShell.view()
	case PageScanner:
		scene = m.scanner.view()
	case PagePetStatus:
		scene = m.petStatus.view()
	default:
		scene = styles.Dim.Render("(unknown page)")
	}

	// Status notification bar at the bottom
	if m.statusMsg != "" {
		notice := lipgloss.NewStyle().
			Foreground(styles.ColGreen).
			Render("  " + m.statusMsg)
		scene += "\n" + notice
	}

	return lipgloss.Place(
		m.width, m.height,
		lipgloss.Center, lipgloss.Center,
		scene,
		lipgloss.WithWhitespaceBackground(styles.ColDarkBG),
	)
}

// Ensure AppModel satisfies tea.Model at compile time.
var _ tea.Model = AppModel{}
