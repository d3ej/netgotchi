# Netgotchi

A pwnagotchi-inspired network utility toolbox with a retro Game Boy Color aesthetic. Built with Python and pygame, it lets you run real network tools (ping, SSH, nmap) from a pixel-art interface while caring for a virtual pet that evolves as you use the tools.

**Tech stack:** Python 3.10+, pygame 2.5+, paramiko (SSH), python-nmap, 160×144 GBC display at 4× scale.

**Key directories:**
- `netgotchi/tools/` — network tool implementations (ping, SSH, nmap scanner)
- `netgotchi/engine/` — renderer, scene manager, input handling, UI components
- `netgotchi/pet/` — pet stats, evolution logic (5 stages: Bit → Byte → Packet → Frame → Stream)

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
