# NetGotchi

A **pwnagotchi-inspired** network utility toolbox with a retro Game Boy Color aesthetic. Run real networking tools (ping, SSH, nmap) from a pixel interface and watch your virtual pet evolve as you improve your tooling.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![pygame](https://img.shields.io/badge/pygame-2.5%2B-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Screenshots

| Overworld | Tools Menu | Ping Tool |
|:-:|:-:|:-:|
| ![Overworld](screenshots/overworld.png) |![Tools](screenshots/tools.png) | ![Ping](screenshots/ping.png) |

---

## Features

- **GBC-authentic display** — 160×144 internal resolution, 4× integer-scaled to 640×576. 4-color palettes, 8×8 pixel sprites, JRPG-style dialog boxes and menus
- **Virtual pet** — Bit hatches from an egg and evolves through 5 stages (Bit → Byte → Packet → Frame → Stream) as you earn XP
- **Real network tools** — Ping hosts, SSH into devices with multi-method authentication and real-time shell streaming, scan networks with nmap
- **Dynamic host discovery** — Reads `~/.ssh/config` and `/etc/hosts` so your real hosts appear in-game
- **Advanced SSH authentication** — Password, public key, and keyboard-interactive auth modes with interactive UI featuring masked password input
- **Real-time shell streaming** — Connect to remote SSH servers, execute commands, and see output stream in real-time within the GBC interface
- **Custom target input** — Enter any host/IP manually across all tools without pre-configuration
- **Save system** — Pet stats persist to JSON between sessions; your pet gets hungry while you're away

## Quickstart

### 1. Clone

```bash
git clone https://github.com/d3ej/netgotchi.git
cd netgotchi
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate    # Linux / macOS
# venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run

```bash
python3 main.py
```

A 640×576 window opens with your pet on the overworld.

### Optional: nmap scanning

The scanner tool wraps the system `nmap` binary. Install it if you want network scanning:

```bash
# Debian / Ubuntu
sudo apt install nmap

# macOS
brew install nmap
```

---

## Controls

| Key(s) | Action |
|--------|--------|
| Arrow keys / WASD | Navigate menus |
| Enter / Z | Confirm / select |
| Escape / X | Cancel / back |
| Space | Open menu |
| Tab | Secondary action |

In the SSH tool, you can:
- Select from discovered hosts (`~/.ssh/config`, `/etc/hosts`) or enter a custom hostname/IP
- Choose your authentication method: **password**, **public key** (`~/.ssh/id_rsa`), or **keyboard-interactive** challenge
- See real-time command output streamed into the GBC display as if it were a retro terminal
- Passwords are securely masked (displayed as asterisks) during input
- All output appears line-by-line in the shell view with scrolling support

---

## SSH Authentication Guide

NetGotchi supports three SSH authentication methods via an interactive authentication UI:

1. **Password Authentication** — Enter your login password (displayed as `*` for security)
2. **Public Key Authentication** — Uses `~/.ssh/id_rsa` or specify a custom key path
3. **Keyboard-Interactive** — For servers with challenge-response auth (e.g., two-factor auth)

### SSH Workflow

1. Select **SSH Tool** from Tools Menu
2. Choose a host from discovered list or **CUSTOM** to enter hostname/IP
3. Fill in authentication fields (auto-populated with defaults where available):
   - Username (from system `$USER` or SSH config)
   - Password (optional, masked input)
   - Key path (defaults to `~/.ssh/id_rsa`)
4. Press **Enter** to move through fields, or **ESC** to cancel
5. Shell session opens with real-time output streaming
6. Type commands, press **Enter** to execute, **ESC** to close

---

## Project Structure

```
netgotchi/
├── main.py                     # Entry point, game loop, all scene classes
├── requirements.txt
├── netgotchi/
│   ├── engine/
│   │   ├── renderer.py         # 160×144 GBC renderer with 4× scaling
│   │   ├── input.py            # Virtual button mapping + text input
│   │   ├── scene.py            # Stack-based scene manager
│   │   └── ui.py               # PixelFont, DialogBox, Menu, StatusBar
│   ├── pet/
│   │   ├── pet.py              # Pet stats, evolution, serialization
│   │   └── sprites.py          # 8×8 palette-indexed sprite data
│   ├── data/
│   │   ├── palettes.py         # 4-color GBC palettes
│   │   └── fonts/              # 04b03.ttf pixel font
│   ├── tools/
│   │   ├── base.py             # Threaded base tool class
│   │   ├── ping.py             # ICMP ping via subprocess
│   │   ├── ssh.py              # SSH via paramiko (multi-auth, streaming shell)
│   │   ├── scanner.py          # Network scanning via python-nmap
│   │   └── hosts.py            # Host discovery from system config
│   ├── rpg/                    # RPG mechanics (planned)
│   └── save/
│       └── state.py            # JSON save/load
└── saves/
    └── netgotchi_save.json     # Auto-generated save file
```

## Pet Evolution

Your pet earns XP every time you use a network tool. As XP accumulates, it evolves:

| Stage | Name | XP Required |
|-------|------|-------------|
| Egg | Bit | 0 |
| Hatchling | Byte | 50 |
| Juvenile | Packet | 200 |
| Adult | Frame | 500 |
| Elder | Stream | 1000 |

Stats like mood, hunger, and energy decay in real time — even when the game is closed. Run tools and feed your pet scan data to keep it happy.

## Adding Tools

Each tool follows a 3-step pattern:

1. **Backend** — Create a class in `netgotchi/tools/` that extends `BaseTool` and implements `_execute(params)`
2. **Scene** — Add a scene class in `main.py` with host/command/result phases
3. **Wire it up** — Add the scene to `ToolMenuScene.TOOLS` and import it

See `ping.py` → `PingScene` for the simplest example, or `ssh.py` → `SSHScene` for one with multi-method authentication and interactive shell streaming.

## Dependencies

| Package | Purpose |
|---------|---------|
| `pygame` | Display, input, audio |
| `paramiko` | SSH connections with multi-auth support |
| `python-nmap` | Network scanning |
| `scapy` | Low-level packet crafting (planned) |
| `psutil` | System/network info (planned) |

## License

MIT
