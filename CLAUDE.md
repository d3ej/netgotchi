# Netgotchi

A pwnagotchi-inspired network utility toolbox with a retro terminal aesthetic.
Built with Go and the Charm.sh TUI stack (Bubbletea, Lip Gloss, Bubbles), it
runs real network tools (ping, SSH, nmap) from a full-screen terminal UI while
caring for a virtual pet that evolves as you use the tools.

**Tech stack:** Go 1.21+, Bubbletea v1.1, Lip Gloss v0.13, Bubbles v0.20,
`golang.org/x/crypto` (SSH), system `ping` and `nmap` binaries.

> **Legacy Python version:** The original pygame implementation lives in
> `main.py` and `netgotchi/` (Python package). The Go TUI is now the primary
> codebase; the Python files are kept for reference only.

---

## Repository Layout

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
│       ├── mainmenu.go        # TOOLS / PET / STATUS / SAVE / QUIT
│       ├── toolmenu.go        # PING / SSH / NMAP / BACK
│       ├── ping.go            # Ping scene (target select → async → result)
│       ├── sshauth.go         # SSH auth scene (host → method → credentials)
│       ├── sshshell.go        # Interactive SSH shell with viewport
│       ├── scanner.go         # Nmap scene (target → scan type → result)
│       └── petstatus.go       # Full-screen pet stats
├── saves/                     # Runtime save data (gitignored)
├── main.py                    # Legacy pygame entry point
└── netgotchi/                 # Legacy Python package
```

---

## Running the Project

```bash
# First-time setup
git submodule update --init --recursive   # populate .claude/agent-skills/

# Go TUI (primary)
go run .

# Legacy pygame (requires Python + deps)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

**Controls (Go TUI):**

| Action | Keys |
|--------|------|
| Navigate | ↑ ↓ or j k |
| Confirm | Enter or Space |
| Back / cancel | Esc or q |
| Quit | Ctrl+C |
| Scroll shell output | PgUp / PgDn |

nmap requires elevated privileges on some systems (`sudo go run .`).

---

## Architecture

### Bubbletea Model/Update/View pattern

```
main.go
  └─ tea.NewProgram(ui.AppModel{}, tea.WithAltScreen())

AppModel.Init()          → starts statTick (5s) + animTick (600ms) cmds
AppModel.Update(msg)     → handles global msgs, delegates to active sub-model
AppModel.View()          → renders active sub-model, centered on terminal
```

### Navigation

`AppModel` maintains a `[]Page` history stack.

- Sub-models emit `navigateMsg{page}` or `backMsg{}` via `tea.Cmd` helpers
  (`cmdNavigate`, `cmdBack`, `cmdNavigateSSHShell`, etc.).
- `AppModel.Update` intercepts these, pushes/pops the history stack, and
  initialises the target sub-model by calling its constructor + `init()`.

**Page enum** (`internal/ui/messages.go`):
`PageOverworld → PageMainMenu → PageToolMenu → PagePing / PageSSHAuth / PageScanner / PagePetStatus`

SSH flow: `PageSSHAuth → PageSSHShell`  
(SSHAuth collects host + credentials, emits `cmdNavigateSSHShell(params)`)

### Async operations

All network tools run in a `tea.Cmd` goroutine and return a result message:

```
pingModel.startPing(target)
  └─ tea.Cmd { return pingResultMsg{tools.RunPing(target, 4)} }

sshShellModel.init()
  └─ connectSSHCmd(params)   → sshConnectedMsg  (or sshConnectErrMsg)
  └─ waitForSSHOutput(ch)    → sshOutputMsg / sshClosedMsg  (loops itself)
```

**Thread safety:** the SSH shell streams output via a buffered Go channel
(`chan string, 64`).  `waitForSSHOutput` is a blocking `tea.Cmd` that reads
one chunk and immediately re-schedules itself, so output arrives frame-by-frame
without locking.

### Tick system

| Message | Interval | Effect |
|---------|----------|--------|
| `statTickMsg` | 5 s | `pet.Update(5)` → hunger/energy decay |
| `animTickMsg` | 600 ms | toggles `animFrame` → sprite animation |

### Styles (`internal/styles/styles.go`)

All Lip Gloss styles live in one place.  Key helpers:

- `styles.Bar(pct, width, fill, empty)` — renders a filled progress bar
- `styles.StatBar(label, pct, width)` — label + bar + percentage string
- Pre-built styles: `styles.Green`, `styles.Red`, `styles.Cyan`, `styles.Dim`,
  `styles.Header`, `styles.AppBox`, `styles.Terminal`, etc.

---

## Pet System (`internal/pet/`)

### Stats

| Stat | Range | Notes |
|------|-------|-------|
| `Mood` | 0–100 | Weighted drift toward hunger×0.4 + energy×0.3 + mood×0.3 |
| `Hunger` | 0–100 | Decays 1 pt/hr; fed by tool use |
| `Energy` | 0–100 | Decays 1 pt/hr; restored by `Rest()` |
| `XP` | 0+ | Earned from tools; drives evolution |
| `Level` | 1+ | `1 + XP/100` |
| `ToolAffinity` | map | `{tool_name: use_count}` |

### Evolution

| Stage | Name | XP threshold |
|-------|------|-------------|
| 0 Egg | Bit | 0 |
| 1 Hatchling | Byte | 100 |
| 2 Juvenile | Packet | 300 |
| 3 Adult | Frame | 900 |
| 4 Elder | Stream | 4 500 |

Evolution is checked in `pet.EarnXP()` and `pet.Update()`.

### ASCII sprites (`internal/pet/sprites.go`)

`GetSprite(stage, anim)` returns a `Sprite{Lines []string}`.  Animation names:
`"idle"`, `"wobble"`, `"happy"`, `"sad"`.  Missing animations fall back to
`"idle"`.

To add sprites for a new stage or animation:
1. Add the `Sprite` entry to the `Sprites` map in `sprites.go`
2. Optionally add a palette color to `spriteColor()` in `overworld.go`

---

## Tool System (`internal/tools/`)

### ToolResult

```go
type ToolResult struct {
    ToolName string
    Success  bool
    Data     map[string]any   // tool-specific result data
    Error    string
    Duration float64
    XPReward int
}
```

### Ping (`ping.go`)

`RunPing(target, count) ToolResult` — calls system `ping` via `os/exec`,
parses RTT avg and packet loss with regex.  XP: 15 (fast <10ms), 10 (success),
5 (attempt).

### SSH (`ssh.go`)

Two modes:

- `RunSSHCommand(params, command) ToolResult` — single command, returns stdout
- `OpenSSHShell(params) (*SSHShell, <-chan string, error)` — interactive shell;
  output channel is closed when the session ends

Auth methods: `"password"`, `"key"` (reads file), `"agent"` (SSH agent + key
files in `~/.ssh/`).

`stripANSI(s)` is applied to all shell output so ANSI escape codes do not
corrupt the viewport.

### Nmap (`scanner.go`)

`RunScan(target, scanType) ToolResult` — calls `nmap -oX -` and parses the
XML output with `encoding/xml`.  Scan types: `ScanQuick` (`-sn`), `ScanPorts`
(`-sT`), `ScanFull` (`-sT -sV -F`).

Result `Data["hosts"]` is `[]ScanHost` with IP, hostname, state, and open ports.

### Host discovery (`hosts.go`)

`DiscoverHosts() []Host` — merges `~/.ssh/config` (Host/HostName/User/Port)
and `/etc/hosts` (skipping loopback and link-local).  Always includes
`localhost (127.0.0.1:22)`.

---

## Save System (`internal/save/state.go`)

`Save(pet, path)` / `Load(path)` — JSON marshal/unmarshal of `*pet.Pet`.
Default path: `saves/netgotchi_save.json` (directory created on first save).
On load, `AppModel.New()` immediately applies offline decay (`pet.Update(elapsed)`).

---

## Code Conventions

- **Standard Go style** — `gofmt`, `go vet` must pass; no linter config.
- **Elm architecture** — every sub-model has `update(msg) (model, tea.Cmd)`
  and `view() string`.  Sub-models are plain structs, not interfaces.
- **No goroutines except tea.Cmd** — all concurrency is expressed as
  `tea.Cmd` returning a message.  The SSH output channel is the only shared
  state between goroutines, and it is read exclusively through `waitForSSHOutput`.
- **No global state** — pet pointer is threaded through constructors.
- **Styles in one place** — add new styles to `internal/styles/styles.go`,
  not inline.
- **Adding a new tool:** create `internal/tools/mytool.go`, add a scene in
  `internal/ui/mytool.go`, add the page to the `Page` enum in `messages.go`,
  wire it into `toolmenu.go` and `app.go`.

---

## Network Team Agents

This project has 5 specialist agents available as project-local agents
(`.claude/agents/`). Delegate to them proactively for tasks in their domain.

> **Setup for new clones:**
> ```bash
> git submodule update --init --recursive
> ```
> This populates `.claude/agent-skills/` so the symlinks in `.claude/agents/` resolve.

### When to use each agent

| Agent | Use when working on… |
|-------|----------------------|
| `net-proto` | SSH auth in `tools/ssh.go`, TCP/ping semantics, nmap scan behaviour |
| `net-devops` | New tool integrations, extending the tools layer, CI |
| `net-offsec` | Security review of SSH key handling, host discovery, scan safety |
| `net-docs` | Runbooks, HLD/LLD for new features, change records |
| `manager` | Multi-domain tasks spanning protocol + automation + security + docs |

### Keeping agents up to date

```bash
git submodule update --remote .claude/agent-skills
git add .claude/agent-skills
git commit -m "Update network agent-skills submodule"
```

---

## Known Gaps / Planned Work

- **Mouse support** — `tea.WithMouseCellMotion()` is enabled; scroll wheel on
  the SSH viewport is wired but not fully tested on all terminals
- **Nmap privileges** — `ScanPorts` / `ScanFull` require root or `CAP_NET_RAW`
  on Linux; `ScanQuick` (`-sn`) works as a normal user on most systems
- **SSH known-hosts** — uses `InsecureIgnoreHostKey()`; production use should
  implement a proper known-hosts callback
- **Adult / Elder sprites** — ASCII art for stages 3 & 4 exists but is minimal;
  feel free to improve `internal/pet/sprites.go`
- **RPG mechanics** — stat-based tool gating, pet items, etc. are not yet implemented
- **Test suite** — `tests/` is empty; new tests should use the standard `testing`
  package with `go test ./...`
