# NetGotchi

A **pwnagotchi-inspired** network utility toolbox with a retro terminal aesthetic. Run real networking tools (ping, SSH, nmap) from a full-screen terminal UI and watch your virtual pet evolve as you use them.

![Go](https://img.shields.io/badge/Go-1.21%2B-blue)
![Bubbletea](https://img.shields.io/badge/Bubbletea-TUI-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Features

- **Terminal UI** — built on [Bubbletea](https://github.com/charmbracelet/bubbletea) and [Lip Gloss](https://github.com/charmbracelet/lipgloss), runs full-screen in any terminal, no display server required
- **Virtual pet** — Bit hatches from an egg and evolves through 5 stages (Bit → Byte → Packet → Frame → Stream) as you earn XP
- **Real network tools** — ping hosts, SSH into devices with password/key/agent authentication and real-time shell streaming, scan networks with nmap
- **Dynamic host discovery** — reads `~/.ssh/config` and `/etc/hosts` so your real hosts show up as SSH targets
- **Custom target input** — enter any host/IP manually across all tools without pre-configuration
- **Care loop, not a gate** — pet stats (mood/hunger/energy) decay in real time, including while the app is closed, and Feed/Rest are meant to be deliberate actions — but tools always work at full functionality regardless of pet condition. This is a real tool with a tamagotchi-style layer on top, not a game that locks you out of pinging something because your pet is sad.
- **Save system** — pet stats persist to JSON between sessions (`saves/netgotchi_save.json`)

## Quickstart

### 1. Clone

```bash
git clone https://github.com/d3ej/netgotchi.git
cd netgotchi
git submodule update --init --recursive   # populate .claude/agent-skills/
```

### 2. Run

```bash
go run .
```

Requires Go 1.21+. Dependencies are fetched automatically via `go.mod`.

### Optional: nmap scanning

The scanner tool wraps the system `nmap` binary. Install it if you want network scanning:

```bash
# Debian / Ubuntu
sudo apt install nmap

# macOS
brew install nmap
```

Port and version scans (`ScanPorts` / `ScanFull`) need elevated privileges on most systems — run with `sudo go run .` if a scan comes back empty. The quick ping-scan (`ScanQuick`, `-sn`) works unprivileged.

---

## Controls

| Key(s) | Action |
|--------|--------|
| ↑ ↓ or j k | Navigate menus |
| Enter or Space | Confirm / select |
| Esc or q | Cancel / back |
| Ctrl+C | Quit |
| PgUp / PgDn | Scroll SSH shell output |

In the SSH tool, you can:
- Select from discovered hosts (`~/.ssh/config`, `/etc/hosts`) or choose **CUSTOM** to type a hostname/IP directly
- Choose your authentication method: **password**, **key file** (defaults to `~/.ssh/id_rsa`), or **agent / auto** (tries `SSH_AUTH_SOCK` first, then common key files in `~/.ssh/`)
- Use **Tab** / **Shift+Tab** (or ↑↓) to move between credential fields, **Enter** to advance or submit
- Watch command output stream into the terminal in real time, with scrollback via PgUp/PgDn
- Password input is masked (`●`) as you type

---

## SSH Authentication Guide

1. Select **SSH** from the Tools menu
2. Choose a host from the discovered list, or **CUSTOM** to enter a hostname/IP
3. Pick an authentication method
4. Fill in the credential fields (username is pre-filled from `$USER` or your SSH config where available)
5. Press **Enter** to move through fields, or **Esc** to go back
6. The shell session opens with real-time output streaming — type commands, **Enter** to send, **Esc**/**Ctrl+C** to disconnect

---

## Project Structure

```
netgotchi/
├── main.go                    # Entry point — wires tea.Program + ui.AppModel
├── go.mod / go.sum            # Go module (github.com/d3ej/netgotchi)
├── internal/
│   ├── styles/styles.go       # Lip Gloss palette + shared style helpers
│   ├── pet/
│   │   ├── pet.go             # Pet struct, stats, evolution, serialization
│   │   └── sprites.go         # ASCII art sprites per evolution stage
│   ├── save/state.go          # JSON save / load (saves/netgotchi_save.json)
│   ├── tools/
│   │   ├── base.go            # ToolResult struct
│   │   ├── hosts.go           # Host discovery (~/.ssh/config, /etc/hosts)
│   │   ├── ping.go            # System ping via os/exec
│   │   ├── ssh.go             # SSH client (golang.org/x/crypto/ssh)
│   │   └── scanner.go         # Nmap via os/exec + XML parsing
│   └── ui/
│       ├── messages.go        # All tea.Msg types + Page enum + cmd helpers
│       ├── app.go             # Root AppModel — navigation stack, ticks, save
│       ├── overworld.go       # Home screen: pet sprite + stat bars
│       ├── mainmenu.go        # TOOLS / STATUS / SAVE / QUIT
│       ├── toolmenu.go        # PING / SSH / NMAP / BACK
│       ├── ping.go            # Ping scene (target select → async → result)
│       ├── sshauth.go         # SSH auth scene (host → method → credentials)
│       ├── sshshell.go        # Interactive SSH shell with viewport
│       ├── scanner.go         # Nmap scene (target → scan type → result)
│       └── petstatus.go       # Full-screen pet stats
└── saves/                     # Runtime save data (gitignored)
```

## Pet Evolution

Your pet earns XP every time you use a network tool. As XP accumulates, it evolves:

| Stage | Name | XP Required |
|-------|------|-------------|
| Egg | Bit | 0 |
| Hatchling | Byte | 100 |
| Juvenile | Packet | 300 |
| Adult | Frame | 900 |
| Elder | Stream | 4,500 |

Mood, hunger, and energy decay in real time — even while the app is closed — but never block tool usage. Run tools (and eventually, deliberate Feed/Rest actions) to keep your pet happy.

## Adding Tools

Each tool follows the same pattern:

1. **Backend** — create `internal/tools/mytool.go` returning a `ToolResult`
2. **Scene** — add `internal/ui/mytool.go` as a Bubbletea sub-model (`update()` / `view()`), following the shape of `ping.go` or `scanner.go`
3. **Wire it up** — add the page to the `Page` enum in `messages.go`, then register it in `toolmenu.go` and in the four switch statements in `app.go`

See `ping.go` for the simplest example (target select → async command → result), or `sshauth.go`/`sshshell.go` for one with multi-method authentication and a streaming interactive session.

## Dependencies

| Package | Purpose |
|---------|---------|
| [`bubbletea`](https://github.com/charmbracelet/bubbletea) | Terminal UI framework (Elm-architecture model/update/view) |
| [`lipgloss`](https://github.com/charmbracelet/lipgloss) | Terminal styling, layout, colors |
| [`bubbles`](https://github.com/charmbracelet/bubbles) | TUI components (text input, viewport, spinner) |
| [`golang.org/x/crypto`](https://pkg.go.dev/golang.org/x/crypto/ssh) | SSH client |
| `ping`, `nmap` | System binaries, invoked via `os/exec` |

## License

MIT
