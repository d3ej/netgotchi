# Netgotchi

A pwnagotchi-inspired network utility toolbox with a retro Game Boy Color aesthetic. Built with Python and pygame, it lets you run real network tools (ping, SSH, nmap) from a pixel-art interface while caring for a virtual pet that evolves as you use the tools.

**Tech stack:** Python 3.10+, pygame 2.5+, paramiko (SSH), python-nmap, 160×144 GBC display at 4× scale.

---

## Repository Layout

```
netgotchi/
├── main.py                  # Entry point + all scene classes (1489 lines)
├── requirements.txt         # Runtime dependencies
├── readme.md                # User-facing docs
├── saves/                   # Runtime save data (gitignored)
├── screenshots/             # Game screenshots
├── tests/                   # Test directory (currently empty)
└── netgotchi/               # Main package
    ├── engine/              # Renderer, scene manager, input, UI components
    ├── pet/                 # Pet stats, evolution, sprite data
    ├── tools/               # Network tool backends (ping, SSH, nmap)
    ├── data/                # Palettes, fonts
    ├── save/                # JSON save/load
    └── rpg/                 # RPG mechanics (planned, empty)
```

**All game scenes live in `main.py`** — this is intentional for simplicity. If scenes are refactored into separate files, place them in a `netgotchi/scenes/` package.

---

## Running the Project

```bash
# First-time setup
git submodule update --init --recursive   # populate .claude/agent-skills/
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run
python3 main.py
```

**Controls:**

| Action | Keys |
|--------|------|
| Navigate | Arrow keys or WASD |
| Confirm (A) | Return or Z |
| Cancel (B) | Escape or X |
| Open menu (START) | Space |
| Secondary (SELECT) | Tab |

nmap requires elevated privileges on some systems (`sudo python3 main.py` or `sudo setcap`).

---

## Architecture

### Game Loop (`main.py` lines 1430–1474)

```
while running:
    events = pygame.event.get()
    input.update(events)           # edge/hold/release detection
    scene_manager.update(input, dt)  # only top scene receives update
    scene_manager.draw(renderer)     # all scenes drawn bottom-to-top
    dt = renderer.present()          # scale to window, cap to 30 FPS, return dt
```

### Scene System (`netgotchi/engine/scene.py`)

Stack-based scene manager. Pushing a scene pauses the one below; popping resumes it. All scenes are drawn bottom-to-top, so overlays (menus) render correctly over the overworld.

**Scene lifecycle:** `on_enter` → `update` / `draw` loop → `on_pause` / `on_resume` (for overlays) → `on_exit`

**Scenes in `main.py`:**

| Scene | Purpose |
|-------|---------|
| `OverworldScene` | Home screen: pet sprite, mood/hunger/energy bars, idle animation |
| `MainMenuScene` | Overlay: TOOLS / PET / STATUS / SAVE / QUIT |
| `ToolMenuScene` | Choose PING / SSH / NMAP |
| `TargetInputScene` | Reusable host/target picker with free-text input |
| `SSHAuthScene` | Multi-step SSH auth (method → credential fields) |
| `PingScene` | Runs ping, streams results |
| `SSHScene` | SSH with 5 phases: host → auth → command/CLI/shell → result |
| `ScannerScene` | Nmap target + scan type → results |
| `PetStatusScene` | Full-screen pet stats display |

### Tool System (`netgotchi/tools/`)

All tools inherit `BaseTool` (`base.py`). The base class provides:
- `run(params, callback)` — spawns a daemon thread; `callback(ToolResult)` is called from that thread
- `xp_reward(result_data)` / `food_value(result_data)` — overridable hooks

**`ToolResult` fields:** `tool_name`, `success`, `data`, `error`, `duration`, `xp_reward`

Scene code must handle `ToolResult` callbacks from a non-main thread (set a flag or queue; never touch pygame surfaces from the worker).

**Adding a new tool:**
1. Create `netgotchi/tools/mytool.py`, subclass `BaseTool`, implement `name` property and `_execute(params)`
2. Create a scene in `main.py` following the PingScene/SSHScene pattern
3. Wire it into `ToolMenuScene`

### Renderer (`netgotchi/engine/renderer.py`)

Internal resolution: **160×144** (Game Boy Color). Display scale: **4×** → 640×576 window.

Two-surface pattern:
1. Draw everything to the 160×144 `gbc_surface`
2. `present()` scales it to the window surface and calls `pygame.display.flip()`

`draw_sprite(sprite_data, palette, x, y, px_size=1)` — palette index 0 is transparent.

### Input (`netgotchi/engine/input.py`)

Virtual button enum: `UP DOWN LEFT RIGHT A B START SELECT`

Useful methods:
- `input.pressed(btn)` — true only on the frame the button was pressed
- `input.held(btn)` — true every frame while held
- `input.text_events` — list of TEXTINPUT strings for text entry scenes
- `input.key_events` — list of KEYDOWN events (for backspace, etc.)

---

## Pet System (`netgotchi/pet/`)

### Stats

| Stat | Range | Notes |
|------|-------|-------|
| `mood` | 0–100 | Weighted average of hunger + energy + current mood |
| `hunger` | 0–100 | Decays ~1 pt/hr; fed by tool use |
| `energy` | 0–100 | Decays ~1 pt/hr; restored by `rest()` |
| `xp` | 0+ | Earned from tools; drives evolution |
| `level` | 0+ | Increases with XP milestones |
| `tool_affinity` | dict | `{tool_name: use_count}` |

### Evolution

| Stage index | Name | XP threshold | Sprites available |
|-------------|------|-------------|-------------------|
| 0 | Bit (egg) | 0 | EGG_IDLE, EGG_WOBBLE |
| 1 | Byte (hatchling) | 100 | HATCHLING_IDLE, HAPPY, SAD |
| 2 | Packet (juvenile) | 300 | JUVENILE_IDLE, HAPPY |
| 3 | Frame (adult) | 900 | *(sprites not yet drawn)* |
| 4 | Stream (elder) | 4500 | *(sprites not yet drawn)* |

Evolution is checked inside `pet.earn_xp()`. `pet.stage` uses the string keys (`"egg"`, `"hatchling"`, etc.) from `STAGES`.

### XP rewards by tool

| Tool | XP |
|------|----|
| Ping — fast (<10 ms avg) | 15 |
| Ping — success | 10 |
| Ping — attempt | 5 |
| SSH — success | 20 |
| SSH — failure | 5 |
| Nmap — 10 + 5 per host found | varies |

### Sprites (`netgotchi/pet/sprites.py`)

8×8 palette-indexed grids (list of lists, values 0–3). Access via `get_sprite(stage, animation)` which returns a safe fallback if the animation is missing.

When adding sprites for Stage 3/4:
- Add grid constants (e.g., `ADULT_IDLE`)
- Register them in the `SPRITES` dict at the bottom of `sprites.py`
- Add matching palette entries in `netgotchi/data/palettes.py`

---

## Palettes (`netgotchi/data/palettes.py`)

All colors are `(r, g, b, a)` tuples. Each palette is a list of 4 colors where index 0 is transparent (alpha=0).

Named palettes: `DMG`, `UI_DEFAULT`, `UI_HEALTH_GREEN/RED`, `UI_XP_BLUE`, `PET_EGG/HATCHLING/JUVENILE`, `TOOL_PING/NMAP/SSH`.

---

## Save System (`netgotchi/save/state.py`)

Saves to `saves/netgotchi_save.json`. Only `Pet` state is serialized (via `pet.to_dict()` / `Pet.from_dict()`). The directory is created on first save; the file is gitignored.

---

## Host Discovery (`netgotchi/tools/hosts.py`)

`discover_hosts()` merges two sources:
1. `~/.ssh/config` — reads `Host`, `HostName`, `User`, `Port` stanzas
2. `/etc/hosts` — skips loopback and link-local (`127.x`, `::1`, `fe80::`, `ff0x::`)

Returns `list[dict]` with keys `name`, `host`, `user`, `port`. Always includes `127.0.0.1 / localhost`.

---

## SSH Tool (`netgotchi/tools/ssh.py`)

Uses paramiko. Three auth methods dispatched separately (not fallback-chained):
- `"password"` — `connect(password=…)`
- `"key"` — `connect(key_filename=…)`
- `"auto"` — lets paramiko try agent + `~/.ssh/` keys

Two operating modes:
- `execute(command)` — single command, returns stdout/stderr/exit_code
- `open_shell(on_output, on_close)` — interactive shell in background thread; `send_command(text)` writes to it; `close_session()` tears it down

---

## UI Components (`netgotchi/engine/ui.py`)

| Class | Key methods |
|-------|------------|
| `PixelFont` | `render(text, color)` — cached surface; uses `04b03.ttf` at size 8 |
| `DialogBox` | `set_text(text)`, `update(dt)`, `draw(renderer)` — typewriter at 30 chars/sec; `skip()` finishes immediately |
| `Menu` | Cursor-based vertical list; UP/DOWN navigation; `selected_item()` |
| `StatusBar` | Percentage bar; call `draw(renderer, x, y, width, height, pct, palette)` |

---

## Code Conventions

- **No type hints** — keeps the code accessible for a learning audience.
- **LEARNING NOTE comments** — present throughout; explain the *why* of patterns. Preserve them.
- **snake_case** for functions/variables/methods; **UPPER_CASE** for module-level constants.
- **No test suite yet** — `tests/` is empty. New tests should use pytest.
- **No linter config** — PEP 8 is the implicit standard.
- **Thread safety** — tool callbacks arrive from daemon threads. Do not call pygame from worker threads; use a flag or `queue.Queue` in the scene.

---

## Network Team Agents

This project has 5 specialist agents available as project-local agents (`.claude/agents/`). Delegate to them proactively for tasks in their domain.

> **Setup for new clones:**
> ```bash
> git submodule update --init --recursive
> ```
> This populates `.claude/agent-skills/` so the symlinks in `.claude/agents/` resolve.

### When to use each agent

| Agent | Use when working on… |
|-------|----------------------|
| `net-proto` | SSH auth flows in `netgotchi/tools/ssh.py`, TCP/ping semantics, nmap scan behaviour, protocol-level debugging |
| `net-devops` | New network tool integrations, automation scripts, extending the tools layer, CI |
| `net-offsec` | Security review of SSH key handling, host discovery exposure, nmap scan safety |
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

- **Adult (Frame) and Elder (Stream) sprites** — not yet drawn; fallback is the juvenile sprite
- **RPG mechanics** — `netgotchi/rpg/` package exists but is empty
- **Test suite** — `tests/` directory exists but has no tests
- **Scapy integration** — listed in requirements, not yet used
- **psutil integration** — listed in requirements, not yet used
