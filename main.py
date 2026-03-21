"""
NetGotchi — Retro Network Engineering Toolkit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Main entry point. Sets up the game loop and scene stack.

LEARNING NOTES — this module teaches:
  - Python's if __name__ == "__main__" pattern
  - The game loop (poll events → update → draw → present)
  - Wiring modules together into a working application
  - Scene-based game architecture in practice

THE GAME LOOP (same pattern as your SDL2 dungeon crawler!):
    while running:
        events = get_events()      # What did the player do?
        update(events, dt)         # Update game state
        draw()                     # Render the frame
        present()                  # Show it on screen
"""

import os
import pygame
import sys
import threading
import time

# ── Engine imports ──────────────────────────────────────────────────────
from netgotchi.engine.renderer import Renderer
from netgotchi.engine.input import Input, A, B, START, UP, DOWN
from netgotchi.engine.scene import Scene, SceneManager
from netgotchi.engine.ui import PixelFont, DialogBox, Menu, StatusBar

# ── Pet imports ─────────────────────────────────────────────────────────
from netgotchi.pet.pet import Pet
from netgotchi.pet.sprites import get_sprite

# ── Data imports ────────────────────────────────────────────────────────
from netgotchi.data.palettes import (
    PET_EGG, PET_HATCHLING, PET_JUVENILE,
    UI_DEFAULT, TOOL_PING, TOOL_NMAP, TOOL_SSH 
)

# ── Tool imports ────────────────────────────────────────────────────────
from netgotchi.tools.ping import PingTool
from netgotchi.tools.ssh import SSHTool, HAS_PARAMIKO
from netgotchi.tools.scanner import ScannerTool
from netgotchi.tools.hosts import discover_hosts

# ── Save imports ────────────────────────────────────────────────────────
from netgotchi.save.state import save_game, load_game, has_save

# ── UI Colors ───────────────────────────────────────────────────────────
WHITE = (255, 255, 255)
GRAY = (140, 140, 160)
CYAN = (100, 220, 255)
GREEN = (50, 255, 50)
RED = (255, 80, 80)
YELLOW = (255, 220, 0)
DARK_BG = (8, 8, 16)

# Map pet stages to their palette
STAGE_PALETTES = {
    "egg": PET_EGG,
    "hatchling": PET_HATCHLING,
    "juvenile": PET_JUVENILE,
}


# ═══════════════════════════════════════════════════════════════════════
#  OVERWORLD SCENE — The main screen showing your pet
# ═══════════════════════════════════════════════════════════════════════
class OverworldScene(Scene):
    """The home screen. Shows your pet, its stats, and waits for input.

    LEARNING NOTE — Scene subclass:
        Each screen in the game is a Scene subclass. It overrides
        update() and draw() to define what happens on that screen.
        The SceneManager calls these methods each frame.
    """

    def __init__(self, game):
        """
        Args:
            game: The Game object (holds shared state like pet, font, tools).
        """
        self.game = game
        self.anim_timer = 0.0
        self.anim_frame = 0  # 0 or 1 for idle animation toggle
        self.dialog = DialogBox(game.font, x=4, y=104, width=152, height=36)
        self._show_welcome = True

    def on_enter(self):
        if self._show_welcome:
            self.dialog.set_text(
                f"{self.game.pet.name} is waiting! "
                f"Press SPACE for menu."
            )
            self._show_welcome = False

    def update(self, input_state, dt):
        # Update pet stats (real-time decay)
        self.game.pet.update(dt)

        # Advance sprite animation (toggle every 0.8 seconds)
        self.anim_timer += dt
        if self.anim_timer >= 0.8:
            self.anim_timer -= 0.8
            self.anim_frame = 1 - self.anim_frame

        # Update dialog typewriter
        self.dialog.update(dt)

        # Enter skips dialog text
        if input_state.pressed(A) and not self.dialog.finished:
            self.dialog.skip()

        # START opens the main menu
        if input_state.pressed(START):
            self.game.scene_manager.push(
                MainMenuScene(self.game)
            )

    def draw(self, renderer):
        renderer.clear(DARK_BG)
        pet = self.game.pet
        font = self.game.font
        surface = renderer.get_surface()

        # ── Header bar ──────────────────────────────────────────────
        renderer.draw_rect(0, 0, 160, 10, (16, 16, 32))
        font.draw(surface, f"Lv.{pet.level} {pet.name}", 2, 1, CYAN)
        font.draw(surface, pet.mood_name.upper(), 110, 1, YELLOW)

        # ── Pet sprite (centered, drawn at 2x pixel size) ──────────
        # Pick animation based on mood
        if pet.mood >= 60:
            anim = "happy" if self.anim_frame else "idle"
        elif pet.mood >= 30:
            anim = "idle"
        else:
            anim = "sad"

        sprite_data = get_sprite(pet.stage, anim)
        palette = STAGE_PALETTES.get(pet.stage, PET_EGG)
        # Center the 8x8 sprite (at px_size=2, it's 16x16 GBC pixels)
        sprite_x = (160 - 8 * 2) // 2
        sprite_y = 35
        renderer.draw_sprite(sprite_data, palette, sprite_x, sprite_y, px_size=2)

        # ── Stats area ──────────────────────────────────────────────
        stats_y = 65

        # Mood bar
        font.draw(surface, "MOOD", 4, stats_y, GRAY)
        mood_bar = StatusBar(30, stats_y + 1, 50, 4,
                             fg_color=GREEN if pet.mood >= 40 else RED)
        mood_bar.draw(surface, pet.mood, 100)

        # Hunger bar
        font.draw(surface, "FOOD", 4, stats_y + 10, GRAY)
        hunger_bar = StatusBar(30, stats_y + 11, 50, 4,
                               fg_color=GREEN if pet.hunger >= 30 else RED)
        hunger_bar.draw(surface, pet.hunger, 100)

        # XP bar
        font.draw(surface, "XP", 4, stats_y + 20, GRAY)
        xp_in_level = pet.xp % 100
        xp_bar = StatusBar(30, stats_y + 21, 50, 4,
                           fg_color=(100, 160, 255))
        xp_bar.draw(surface, xp_in_level, 100)

        # Quick stats on the right side
        font.draw(surface, f"STG:{pet.stage[:4].upper()}", 95, stats_y, GRAY)
        font.draw(surface, f"PNG:{pet.total_pings}", 95, stats_y + 10, GRAY)
        font.draw(surface, f"SCN:{pet.total_scans}", 95, stats_y + 20, GRAY)

        # ── Dialog box ──────────────────────────────────────────────
        self.dialog.draw(surface)


# ═══════════════════════════════════════════════════════════════════════
#  MAIN MENU SCENE — JRPG-style command menu
# ═══════════════════════════════════════════════════════════════════════
class MainMenuScene(Scene):
    """The pause/command menu — overlays on top of the overworld.

    LEARNING NOTE — overlay pattern:
        This scene doesn't clear the screen. The overworld scene below
        draws first (because SceneManager draws all scenes bottom-to-top),
        then this menu draws on top. This gives us that classic JRPG
        feel where the menu floats over the game world.
    """

    ITEMS = ["TOOLS", "PET", "STATUS", "SAVE", "QUIT"]

    def __init__(self, game):
        self.game = game
        self.menu = Menu(game.font, self.ITEMS, x=90, y=14, width=66)

    def update(self, input_state, dt):
        result = self.menu.update(input_state)

        # Escape closes menu
        if self.menu.cancelled:
            self.game.scene_manager.pop()
            return

        if result is not None:
            choice = self.ITEMS[result]
            if choice == "TOOLS":
                self.game.scene_manager.push(ToolMenuScene(self.game))
            elif choice == "PET":
                self.game.scene_manager.push(PetStatusScene(self.game))
            elif choice == "STATUS":
                self.game.scene_manager.push(PetStatusScene(self.game))
            elif choice == "SAVE":
                save_game(self.game.pet)
                self.game.scene_manager.pop()
                # Show save confirmation on overworld
                overworld = self.game.scene_manager.current
                if hasattr(overworld, "dialog"):
                    overworld.dialog.set_text("Game saved!")
            elif choice == "QUIT":
                save_game(self.game.pet)
                self.game.running = False

    def draw(self, renderer):
        # Don't clear — draws over overworld
        # Semi-transparent overlay for "paused" feel
        surface = renderer.get_surface()
        overlay = pygame.Surface((160, 144), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        surface.blit(overlay, (0, 0))

        self.menu.draw(surface)


# ═══════════════════════════════════════════════════════════════════════
#  TOOL MENU SCENE — Choose which network tool to run
# ═══════════════════════════════════════════════════════════════════════
class ToolMenuScene(Scene):
    """Select a network tool to run."""

    TOOLS = ["PING", "SSH", "NMAP", "BACK"]

    def __init__(self, game):
        self.game = game
        self.menu = Menu(game.font, self.TOOLS, x=4, y=14, width=66)

    def update(self, input_state, dt):
        result = self.menu.update(input_state)

        if self.menu.cancelled:
            self.game.scene_manager.pop()
            return

        if result is not None:
            choice = self.TOOLS[result]
            if choice == "PING":
                self.game.scene_manager.push(
                    PingScene(self.game)
                )
            elif choice == "SSH":
                self.game.scene_manager.push(
                    SSHScene(self.game)
                )
            elif choice == "NMAP":
                self.game.scene_manager.push(
                    ScannerScene(self.game)
                )
            elif choice == "BACK":
                self.game.scene_manager.pop()

    def draw(self, renderer):
        surface = renderer.get_surface()
        overlay = pygame.Surface((160, 144), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        surface.blit(overlay, (0, 0))

        font = self.game.font
        font.draw(surface, "= NETWORK TOOLS =", 30, 4, CYAN)
        self.menu.draw(surface)


# ═══════════════════════════════════════════════════════════════════════
#  TARGET INPUT SCENE — reusable host/target entry
# ═══════════════════════════════════════════════════════════════════════
class TargetInputScene(Scene):
    """Reusable target selection + custom typing scene."""

    def __init__(self, game, title, targets=None, callback=None, start_custom=False):
        self.game = game
        self.title = title
        self.callback = callback
        self.targets = list(targets or []) + ["CUSTOM", "BACK"]
        self.menu = Menu(game.font, self.targets, x=4, y=24, width=100)
        self.dialog = DialogBox(game.font, x=4, y=104, width=152, height=36)

        self.phase = "custom" if start_custom else "menu"
        self._host_buffer = ""
        self._cursor_timer = 0.0
        self._cursor_visible = True

        if start_custom:
            # BUG FIX — Enable key repeat immediately for custom entry
            # Previously: key repeat only enabled when manually selecting
            # "CUSTOM" from menu. Now it's enabled at init if start_custom=True,
            # ensuring first text input doesn't hang/fail to capture input.
            pygame.key.set_repeat(400, 50)
            self.dialog.set_text("Type host/IP and press Enter")
        else:
            self.dialog.set_text("Select target or type custom:")

    def on_exit(self):
        """Clean up when leaving target input scene.

        BUG FIX — Key repeat persistence
        Disables pygame.key.set_repeat() on exit to prevent the repeater
        from persisting into the next scene (which would cause input to fail
        if the next scene doesn't expect it). Each text-input scene now
        manages its own key repeat lifecycle.
        """
        pygame.key.set_repeat(0)

    def _submit_custom(self, target):
        if target.strip():
            self.game.scene_manager.pop()
            self.callback(target.strip())

    def update(self, input_state, dt):
        self.dialog.update(dt)

        if self.phase == "custom":
            for char in input_state.text_events:
                if len(self._host_buffer) < 60:
                    self._host_buffer += char

            for event in input_state.key_events:
                if event.key == pygame.K_BACKSPACE:
                    self._host_buffer = self._host_buffer[:-1]
                elif event.key == pygame.K_RETURN:
                    self._submit_custom(self._host_buffer)
                    return
                elif event.key == pygame.K_ESCAPE:
                    self._host_buffer = ""
                    self.phase = "menu"
                    self.dialog.set_text("Select target or type custom:")
                    return

            self._cursor_timer += dt
            if self._cursor_timer >= 0.5:
                self._cursor_timer -= 0.5
                self._cursor_visible = not self._cursor_visible
            return

        # menu phase
        result = self.menu.update(input_state)

        if self.menu.cancelled:
            self.game.scene_manager.pop()
            return

        if result is not None:
            choice = self.targets[result]
            if choice == "BACK":
                self.game.scene_manager.pop()
            elif choice == "CUSTOM":
                pygame.key.set_repeat(400, 50)
                self.phase = "custom"
                self._host_buffer = ""
                self.dialog.set_text("Type host/IP and press Enter")
            else:
                self.callback(choice)
                self.game.scene_manager.pop()

    def draw(self, renderer):
        renderer.clear(DARK_BG)
        font = self.game.font
        surface = renderer.get_surface()

        renderer.draw_rect(0, 0, 160, 10, (8, 30, 8))
        font.draw(surface, f"[ {self.title} ]", 24, 1, CYAN)

        if self.phase == "menu":
            self.menu.draw(surface)
        else:
            cursor = "_" if self._cursor_visible else " "
            visible = self._host_buffer[-22:]
            font.draw(surface, "Host:", 4, 16, GREEN)
            font.draw(surface, f"{visible}{cursor}", 4, 28, WHITE)
            font.draw(surface, "ENTER=go ESC=back", 20, 42, GRAY)

        self.dialog.draw(surface)


# ═══════════════════════════════════════════════════════════════════════
#  SSH AUTH SCENE — Enter username/password/key path for SSH
# ═══════════════════════════════════════════════════════════════════════
class SSHAuthScene(Scene):
    """Collect SSH credentials from the user with masked password input.

    ADDED FEATURE — Interactive SSH Authentication UI
        Prompts user for three auth fields in sequence:
        1. Username (default from system $USER or host config)
        2. Password (displayed as asterisks for security)
        3. Private key path (default ~/.ssh/id_rsa)

    Flow:
        - User navigates fields with UP/DOWN arrows
        - ENTER moves to next field or submits all three
        - ESC cancels and returns to host selection
        - Password is masked but stored in auth_data
        - Keyboard-interactive flag set if password provided

    Integration:
        - Called by SSHScene when host is selected (via _prompt_auth)
        - Callback (_on_auth_done) wires auth_data into _start_shell()
        - Enables pygame.key.set_repeat() for text input
        - Cleans up with on_exit() to prevent key repeat persistence bugs
    """

    FIELDS = ["username", "password", "pkey_path"]

    def __init__(self, game, host_info, callback):
        self.game = game
        self.host_info = host_info
        self.callback = callback
        self.field_index = 0
        self.values = {
            "username": host_info.get("user") or os.getenv("USER", "admin"),
            "password": "",
            "pkey_path": "~/.ssh/id_rsa",
        }
        self.dialog = DialogBox(game.font, x=4, y=104, width=152, height=36)
        self.dialog.set_text(f"Auth for {host_info.get('name', host_info.get('host', 'host'))}")
        self._cursor_timer = 0.0
        self._cursor_visible = True
        pygame.key.set_repeat(400, 50)

    def on_exit(self):
        """Clean up when leaving auth scene.

        BUG FIX — Key repeat persistence
        Disables pygame.key.set_repeat() on exit to prevent the repeater
        from persisting into the next scene. Without this, key repeat would
        remain active and break input in scenes that don't expect it.
        """
        pygame.key.set_repeat(0)

    def update(self, input_state, dt):
        self.dialog.update(dt)

        if input_state.pressed(B):
            self.game.scene_manager.pop()
            return

        # Handle character entry for active field
        current_field = self.FIELDS[self.field_index]

        for char in input_state.text_events:
            if current_field == "password":
                if len(self.values["password"]) < 60:
                    self.values["password"] += char
            else:
                if len(self.values[current_field]) < 60:
                    self.values[current_field] += char

        for event in input_state.key_events:
            if event.key == pygame.K_BACKSPACE:
                self.values[current_field] = self.values[current_field][:-1]
            elif event.key == pygame.K_RETURN:
                if self.field_index < len(self.FIELDS) - 1:
                    self.field_index += 1
                else:
                    # Submit
                    auth_data = {
                        "username": self.values["username"].strip(),
                        "password": self.values["password"],
                        "pkey_path": self.values["pkey_path"].strip(),
                        "keyboard_interactive": bool(self.values["password"]),
                    }
                    self.game.scene_manager.pop()
                    self.callback(self.host_info, auth_data)
                    return
            elif event.key == pygame.K_ESCAPE:
                self.game.scene_manager.pop()
                return
            elif event.key == pygame.K_UP:
                self.field_index = max(0, self.field_index - 1)
            elif event.key == pygame.K_DOWN:
                self.field_index = min(len(self.FIELDS) - 1, self.field_index + 1)

        self._cursor_timer += dt
        if self._cursor_timer >= 0.5:
            self._cursor_timer -= 0.5
            self._cursor_visible = not self._cursor_visible

    def draw(self, renderer):
        renderer.clear(DARK_BG)
        font = self.game.font
        surface = renderer.get_surface()

        renderer.draw_rect(0, 0, 160, 10, (8, 30, 8))
        font.draw(surface, "[ SSH AUTH ]", 40, 1, CYAN)

        y = 20
        for i, field in enumerate(self.FIELDS):
            label = field.replace("_", " ").title()
            value = self.values[field]
            if field == "password":
                value = "*" * len(value)

            prefix = ">" if i == self.field_index else " "
            font.draw(surface, f"{prefix} {label}: {value[:18]}", 4, y, GREEN if i == self.field_index else WHITE)
            y += 10

        cursor = "_" if self._cursor_visible else " "
        current = self.FIELDS[self.field_index]
        displayed = self.values[current]
        if current == "password":
            displayed = "*" * len(displayed)
        if len(displayed) > 24:
            displayed = displayed[-24:]

        font.draw(surface, f"{current}: {displayed}{cursor}", 4, 90, YELLOW)
        font.draw(surface, "ENTER=next/done UP/DOWN switch", 4, 100, GRAY)
        font.draw(surface, "ESC=cancel", 4, 110, GRAY)

        self.dialog.draw(surface)


# ═══════════════════════════════════════════════════════════════
#  PING SCENE — Run a ping and show results
# ═══════════════════════════════════════════════════════════════════════
class PingScene(Scene):
    """Interactive ping tool scene.

    LEARNING NOTE — tool execution flow:
        1. Show target input (hardcoded for now, text input coming later)
        2. Start ping in background thread
        3. Show "pinging..." animation while waiting
        4. Display results when done
        5. Award XP to pet
    """

    # Pre-defined targets for easy selection
    TARGETS = ["8.8.8.8", "1.1.1.1", "127.0.0.1", "CUSTOM", "BACK"]

    def __init__(self, game):
        self.game = game
        self.menu = Menu(game.font, self.TARGETS, x=4, y=24, width=80)
        self.ping_tool = PingTool()
        self.result = None
        self.waiting = False
        self.dialog = DialogBox(game.font, x=4, y=104, width=152, height=36)
        self.dialog.set_text("Select target to ping:")
        self.dot_timer = 0.0
        self.dot_count = 0

    def _on_ping_done(self, result):
        """Callback from ping thread.

        LEARNING NOTE — thread safety:
            This function is called from the WORKER THREAD, not the main
            thread. We just store the result — the main thread's update()
            will read it next frame. Simple and safe!
        """
        self.result = result
        self.waiting = False

    def update(self, input_state, dt):
        self.dialog.update(dt)

        if self.waiting:
            # Animate dots while pinging
            self.dot_timer += dt
            if self.dot_timer >= 0.3:
                self.dot_timer -= 0.3
                self.dot_count = (self.dot_count + 1) % 4
            return

        if self.result is not None:
            # Results are in — process them
            if input_state.pressed(A) or input_state.pressed(B):
                # Show result, then award XP and go back
                pet = self.game.pet
                if self.result.success:
                    pet.earn_xp(self.result.xp_reward, "ping")
                    rtt = self.result.data.get("avg_rtt_ms")
                    pet.react_to_ping(True, rtt)
                else:
                    pet.react_to_ping(False)
                self.game.scene_manager.pop()
            return

        # Menu selection
        result = self.menu.update(input_state)

        if self.menu.cancelled:
            self.game.scene_manager.pop()
            return

        if result is not None:
            choice = self.TARGETS[result]
            if choice == "BACK":
                self.game.scene_manager.pop()
            elif choice == "CUSTOM":
                self.game.scene_manager.push(
                    TargetInputScene(
                        self.game,
                        "PING",
                        [t for t in self.TARGETS if t not in ("CUSTOM", "BACK")],
                        self._start_ping,
                        start_custom=True,
                    )
                )
            else:
                self._start_ping(choice)

    def _start_ping(self, target):
        self.waiting = True
        self.result = None
        self.dialog.set_text(f"Pinging {target}...")
        self.ping_tool.run(
            {"target": target, "count": 4},
            callback=self._on_ping_done,
        )

    def draw(self, renderer):
        renderer.clear(DARK_BG)
        font = self.game.font
        surface = renderer.get_surface()

        # Header
        renderer.draw_rect(0, 0, 160, 10, (16, 32, 16))
        font.draw(surface, "[ PING TOOL ]", 40, 1, GREEN)

        if self.waiting:
            # Show pinging animation
            dots = "." * self.dot_count
            font.draw(surface, f"Pinging{dots}", 50, 60, YELLOW)
        elif self.result is not None:
            # Show results
            self._draw_results(surface, font)
        else:
            # Show target menu
            font.draw(surface, "Target:", 4, 16, GRAY)
            self.menu.draw(surface)

        self.dialog.draw(surface)

    def _draw_results(self, surface, font):
        """Draw ping results on screen."""
        y = 20
        if self.result.success:
            data = self.result.data
            font.draw(surface, "PING OK!", 4, y, GREEN)
            y += 12

            rtt = data.get("rtt_avg", "?")
            font.draw(surface, f"RTT: {rtt}ms", 4, y, WHITE)
            y += 10

            loss = data.get("packet_loss", "?")
            loss_color = GREEN if loss == 0 else RED
            font.draw(surface, f"Loss: {loss}%", 4, y, loss_color)
            y += 10

            font.draw(surface, f"+{self.result.xp_reward} XP", 4, y, CYAN)
            y += 12

            font.draw(surface, f"Time: {self.result.duration:.1f}s", 4, y, GRAY)
            y += 12

            # Echo raw ping output into UI
            raw_output = data.get("raw_output", "").strip()
            if raw_output:
                font.draw(surface, "RAW OUTPUT:", 4, y, GRAY)
                y += 10
                for line in raw_output.splitlines()[:3]:
                    font.draw(surface, line[:28], 4, y, WHITE)
                    y += 8
        else:
            font.draw(surface, "PING FAILED!", 4, y, RED)
            y += 12
            err = str(self.result.error)[:25]
            font.draw(surface, err, 4, y, RED)

        font.draw(surface, "Press Enter/Esc to continue", 20, 108, GRAY)


# ═══════════════════════════════════════════════════════════════════════
#  SSH SCENE — Connect to a device and run a command
# ═══════════════════════════════════════════════════════════════════════
class SSHScene(Scene):
    """Interactive SSH tool scene.

    LEARNING NOTE — multi-step scene:
        This scene has 3 phases, controlled by self.phase:
          "host"    → pick a target host
          "command" → pick a command to run
          "result"  → show output and award XP

        Each phase draws different UI. This is a simple state machine
        inside a scene — a common pattern in JRPG menus.
    """

    COMMANDS = [
        "whoami",
        "hostname",
        "uptime",
        "ip addr",
        "uname -a",
        "CLI",
        "BACK",
    ]

    def __init__(self, game):
        self.game = game
        self.ssh_tool = SSHTool()
        self.result = None
        self.waiting = False
        self.phase = "host"  # "host" → "command" → "result"

        # Discover hosts from ~/.ssh/config and /etc/hosts
        # LEARNING NOTE — dynamic menu items:
        #   Instead of a hardcoded list, we read the user's actual
        #   system config at scene creation time. This means new hosts
        #   added to ~/.ssh/config or /etc/hosts appear automatically.
        self._hosts = discover_hosts()
        
        host_labels = [h["name"] for h in self._hosts] + ["CUSTOM", "BACK"]
        self.host_menu = Menu(game.font, host_labels, x=4, y=24, width=90)
        self.cmd_menu = Menu(game.font, self.COMMANDS, x=4, y=24, width=80)
        self.dialog = DialogBox(game.font, x=4, y=104, width=152, height=36)
        self.dialog.set_text("Select SSH target:")

        self.selected_host = None  # Will be a dict from discover_hosts()
        self.selected_cmd = None
        self.dot_timer = 0.0
        self.dot_count = 0
        self.scroll_offset = 0  # For scrolling long output

        # Interactive shell state
        self.shell_session = None
        self.shell_buffer = ""
        self.shell_output_lines = []
        self.shell_scroll = 0
        self.auth_data = None

        # CLI typing state
        self._cli_buffer = ""       # What the user has typed so far
        self._cursor_timer = 0.0    # Timer for blinking cursor
        self._cursor_visible = True # Cursor blink state

    def _on_ssh_done(self, result):
        """Callback from SSH worker thread."""
        self.result = result
        self.waiting = False

    def _on_custom_host(self, hostname):
        """Callback when user enters custom hostname in TargetInputScene.

        ADDED FEATURE — Custom Host Authentication Flow
            Wraps custom hostname into host_info dict, then immediately
            pushes SSHAuthScene for credential collection.
        """
        self.selected_host = {
            "name": hostname,
            "host": hostname,
            "port": 22,
            "user": None,
        }
        self.game.scene_manager.push(
            SSHAuthScene(self.game, self.selected_host, self._on_auth_done)
        )

    def _on_auth_done(self, host_info, auth_data):
        """Callback when user submits auth form in SSHAuthScene.

        ADDED FEATURE — Auth → Shell Bridge
            Stores auth_data (username, password, pkey_path, keyboard_interactive)
            into scene state, then initiates _start_shell() which passes these
            credentials into SSHTool.open_shell().
        """
        self.selected_host = host_info
        self.auth_data = auth_data
        self._start_shell()

    def _prompt_auth(self, host_info):
        """Push auth scene for a given host.

        ADDED FEATURE — Unified Auth Entry Point
            Called for both discovered hosts and custom hosts.
            Prevents code duplication by centralizing SSHAuthScene creation.
        """
        self.game.scene_manager.push(
            SSHAuthScene(self.game, host_info, self._on_auth_done)
        )

    def _append_shell_output(self, text):
        for line in text.splitlines(True):
            if line.endswith("\n"):
                self.shell_output_lines.append(line.rstrip("\n"))
            else:
                if self.shell_output_lines:
                    self.shell_output_lines[-1] += line
                else:
                    self.shell_output_lines.append(line)

        # Keep history manageable
        if len(self.shell_output_lines) > 100:
            self.shell_output_lines = self.shell_output_lines[-100:]

    def _on_shell_output(self, chunk):
        self._append_shell_output(chunk)

    def _on_shell_close(self, success, error):
        if not success and error:
            self._append_shell_output(f"Shell error: {error}")

        self.shell_session = None
        self.dialog.set_text("SSH session closed. Press Esc to go back.")
        self.phase = "host"

    def _start_shell(self):
        """Initiate interactive SSH shell with credentials.

        ADDED FEATURE — Real-time SSH Shell Streaming
            Opens an interactive shell session via SSHTool.open_shell(),
            which runs in a background thread and streams output through
            on_output callbacks. User can type commands and see responses
            incrementally (not batch).

        Auth Integration:
            Pulls username, password, pkey_path, and keyboard_interactive
            from auth_data dict (populated by SSHAuthScene._on_auth_done).
            Falls back to host_info or default values if auth_data is empty
            (allows quick-connect without auth if desired).

        Session Callbacks:
            - on_output: appends chunks to shell_output_lines (UI update)
            - on_close: signals shell end, returns to host selection menu
        """
        if not self.selected_host:
            return

        self.phase = "shell"
        self.shell_output_lines = []
        self.shell_buffer = ""
        self.shell_scroll = 0
        self.dialog.set_text(f"Connecting to {self.selected_host['name']}...")

        params = {
            "host": self.selected_host["host"],
            "port": self.selected_host.get("port", 22),
            "username": (self.auth_data or {}).get("username") or self.selected_host.get("user") or None,
            "password": (self.auth_data or {}).get("password"),
            "pkey_path": (self.auth_data or {}).get("pkey_path"),
            "keyboard_interactive": (self.auth_data or {}).get("keyboard_interactive", False),
            "allow_agent": True,
            "look_for_keys": True,
        }

        self.shell_session = self.ssh_tool.open_shell(
            params,
            on_output=self._on_shell_output,
            on_close=self._on_shell_close,
        )

    def _cleanup_shell(self):
        if self.shell_session and "close" in self.shell_session:
            self.shell_session["close"]()
        self.shell_session = None

    def on_exit(self):
        """Clean up when leaving the SSH scene."""
        self._cleanup_shell()
        pygame.key.set_repeat(0)  # Ensure key repeat is off

    def _run_ssh_command(self, command):
        """Launch an SSH command in a background thread.

        LEARNING NOTE — DRY principle (Don't Repeat Yourself):
            Both preset commands and CLI commands need the same SSH
            setup logic. Extracting it into a helper avoids duplicating
            the host/port/user parameter assembly code.
        """
        self.selected_cmd = command
        self.waiting = True
        self.phase = "result"
        self.scroll_offset = 0
        h = self.selected_host
        self.dialog.set_text(f"SSH {h['name']}...")
        params = {
            "host": h["host"],
            "port": h["port"],
            "command": command,
        }
        if h.get("user"):
            params["username"] = h["user"]
        self.ssh_tool.run(params, callback=self._on_ssh_done)

    def _submit_cli_command(self):
        """Submit the typed CLI buffer as an SSH command."""
        # Disable key repeat when leaving CLI mode
        pygame.key.set_repeat(0)
        self._run_ssh_command(self._cli_buffer.strip())

    def update(self, input_state, dt):
        self.dialog.update(dt)

        if self.waiting:
            self.dot_timer += dt
            if self.dot_timer >= 0.3:
                self.dot_timer -= 0.3
                self.dot_count = (self.dot_count + 1) % 4
            return

        # ── Result phase: show output, scroll with UP/DOWN ──────────
        if self.phase == "result" and self.result is not None:
            if input_state.pressed(UP):
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif input_state.pressed(DOWN):
                self.scroll_offset += 1
            elif input_state.pressed(A) or input_state.pressed(B):
                pet = self.game.pet
                if self.result.success and self.result.data.get("connected"):
                    pet.earn_xp(self.result.xp_reward, "ssh")
                    pet.mood = min(100, pet.mood + 5)
                self.game.scene_manager.pop()
            return

        # ── Host selection phase ────────────────────────────────────
        if self.phase == "host":
            result = self.host_menu.update(input_state)
            if self.host_menu.cancelled:
                self.game.scene_manager.pop()
                return
            if result is not None:
                if result < len(self._hosts):
                    self.selected_host = self._hosts[result]
                    self._prompt_auth(self.selected_host)
                elif result == len(self._hosts):
                    # CUSTOM target path
                    self.game.scene_manager.push(
                        TargetInputScene(
                            self.game,
                            "SSH",
                            [h["name"] for h in self._hosts],
                            self._on_custom_host,
                            start_custom=True,
                        )
                    )
                else:
                    self.game.scene_manager.pop()
            return

        # ── Shell interactive phase ─────────────────────────────────
        if self.phase == "shell":
            # Scrolling output with arrows
            if input_state.pressed(UP):
                self.shell_scroll = max(0, self.shell_scroll - 1)
            elif input_state.pressed(DOWN):
                self.shell_scroll += 1

            # Type commands into local buffer
            for char in input_state.text_events:
                if len(self.shell_buffer) < 80:
                    self.shell_buffer += char

            for event in input_state.key_events:
                if event.key == pygame.K_BACKSPACE:
                    self.shell_buffer = self.shell_buffer[:-1]
                elif event.key == pygame.K_RETURN:
                    line = self.shell_buffer.strip()
                    if line:
                        self._append_shell_output(f"$ {line}")
                        if self.shell_session and self.shell_session.get("send"):
                            self.shell_session["send"](line + "\n")
                        self.shell_buffer = ""
                    return
                elif event.key == pygame.K_ESCAPE:
                    self._cleanup_shell()
                    self.phase = "host"
                    self.shell_buffer = ""
                    self.dialog.set_text("Select SSH target:")
                    return

            # Blink cursor timer
            self._cursor_timer += dt
            if self._cursor_timer >= 0.5:
                self._cursor_timer -= 0.5
                self._cursor_visible = not self._cursor_visible
            return

        # ── Command selection phase ─────────────────────────────────
        if self.phase == "command":
            result = self.cmd_menu.update(input_state)
            if self.cmd_menu.cancelled:
                self.phase = "host"
                self.dialog.set_text("Select SSH target:")
                return
            if result is not None:
                choice = self.COMMANDS[result]
                if choice == "BACK":
                    self.phase = "host"
                elif choice == "CLI":
                    pygame.key.set_repeat(400, 50)
                    self._cli_buffer = ""
                    self._cursor_timer = 0.0
                    self._cursor_visible = True
                    self.phase = "cli"
                    self.dialog.set_text("Type cmd, ENTER=run:")
                else:
                    self.selected_cmd = choice
                    self._run_ssh_command(self.selected_cmd)

    def draw(self, renderer):
        renderer.clear(DARK_BG)
        font = self.game.font
        surface = renderer.get_surface()

        # Header — green like a terminal
        renderer.draw_rect(0, 0, 160, 10, (0, 20, 0))
        font.draw(surface, "[ SSH TOOL ]", 44, 1, GREEN)

        if self.waiting:
            dots = "." * self.dot_count
            font.draw(surface, f"Connecting{dots}", 40, 60, GREEN)

        elif self.phase == "result" and self.result is not None:
            self._draw_results(surface, font)

        elif self.phase == "host":
            font.draw(surface, "Target:", 4, 16, GRAY)
            self.host_menu.draw(surface)

        elif self.phase == "cli":
            name = self.selected_host["name"]
            font.draw(surface, f"Host: {name}", 4, 16, GREEN)
            font.draw(surface, "$", 4, 28, GREEN)

            # Draw typed text with blinking cursor
            # LEARNING NOTE — string slicing for visible window:
            #   The GBC screen is only ~28 chars wide. If the user
            #   types more than that, we show the rightmost portion
            #   so the cursor is always visible.
            max_chars = 25  # Leave room for "$ " prefix and cursor
            visible_text = self._cli_buffer[-max_chars:]
            cursor = "_" if self._cursor_visible else " "
            font.draw(surface, f" {visible_text}{cursor}", 10, 28, WHITE)

            font.draw(surface, "ENTER=run ESC=back", 20, 42, GRAY)

        elif self.phase == "shell":
            name = self.selected_host["name"] if self.selected_host else "unknown"
            font.draw(surface, f"SSH: {name}", 4, 16, GREEN)

            # Show shell history (scrollable)
            max_lines = 8
            start = max(0, len(self.shell_output_lines) - max_lines - self.shell_scroll)
            visible_lines = self.shell_output_lines[start:start + max_lines]
            y = 26
            for line in visible_lines:
                font.draw(surface, line[:28], 4, y, WHITE)
                y += 10

            # Command entry line
            cursor = "_" if self._cursor_visible else " "
            visible_cmd = self.shell_buffer[-22:]
            font.draw(surface, f"> {visible_cmd}{cursor}", 4, 100, CYAN)
            font.draw(surface, "ENTER=send ESC=back", 20, 110, GRAY)

        elif self.phase == "command":
            name = self.selected_host["name"]
            font.draw(surface, f"Host: {name}", 4, 16, GREEN)
            self.cmd_menu.draw(surface)

        self.dialog.draw(surface)

    def _draw_results(self, surface, font):
        """Draw SSH output with scrolling."""
        y = 14
        if self.result.success and self.result.data.get("connected"):
            data = self.result.data
            font.draw(surface, f"$ {data.get('command', '?')}", 4, y, GREEN)
            y += 10

            # Split output into lines and show with scroll
            output = data.get("output", "")
            lines = output.split("\n")
            # Clamp scroll offset
            max_visible = 7
            max_scroll = max(0, len(lines) - max_visible)
            self.scroll_offset = min(self.scroll_offset, max_scroll)

            visible = lines[self.scroll_offset:self.scroll_offset + max_visible]
            for line in visible:
                # Truncate long lines to fit 160px width
                font.draw(surface, line[:28], 4, y, WHITE)
                y += 10

            if len(lines) > max_visible:
                font.draw(surface, "[UP/DOWN scroll]", 35, 90, GRAY)

            font.draw(surface, f"+{self.result.xp_reward} XP", 4, 92, CYAN)
        else:
            font.draw(surface, "SSH FAILED!", 4, y, RED)
            y += 12
            err_msg = ""
            if self.result.data:
                err_msg = str(self.result.data.get("output", ""))[:25]
            elif self.result.error:
                err_msg = str(self.result.error)[:25]
            font.draw(surface, err_msg, 4, y, RED)

        font.draw(surface, "Press Enter/Esc to continue", 20, 100, GRAY)
class ScannerScene(Scene):
    """Nmap scanning scene with target selection and results."""

    TARGETS = ["127.0.0.1", "192.168.1.0/24", "10.0.0.0/24", "CUSTOM", "BACK"]
    SCAN_TYPES = ["quick", "ports", "full"]

    def __init__(self, game):
        self.game = game
        self.scanner_tool = ScannerTool()

        self.phase = "target"  # target / scan_type / waiting / result
        self.selected_target = None
        self.selected_scan_type = None

        self.target_menu = Menu(game.font, self.TARGETS, x=4, y=24, width=100)
        self.scan_menu = Menu(game.font, self.SCAN_TYPES + ["BACK"], x=4, y=24, width=100)

        self.result = None
        self.waiting = False
        self.dot_timer = 0.0
        self.dot_count = 0

        self.dialog = DialogBox(game.font, x=4, y=104, width=152, height=36)
        self.dialog.set_text("Select target to scan:")

    def _on_scan_done(self, result):
        self.result = result
        self.waiting = False

        if result.success:
            pet = self.game.pet
            pet.earn_xp(result.xp_reward, "nmap")
            if isinstance(result.data, dict):
                pet.react_to_scan(result.data.get("host_count", 0))

        self.phase = "result"

    def _start_scan(self):
        self.waiting = True
        self.result = None
        self.phase = "waiting"
        self.dot_timer = 0.0
        self.dot_count = 0
        self.dialog.set_text(f"Scanning {self.selected_target} ({self.selected_scan_type})...")

        self.scanner_tool.run(
            {
                "target": self.selected_target,
                "scan_type": self.selected_scan_type,
            },
            callback=self._on_scan_done,
        )

    def _on_custom_target(self, target):
        self.selected_target = target
        self.phase = "scan_type"
        self.dialog.set_text(f"Target: {target}. Choose type:")

    def update(self, input_state, dt):
        self.dialog.update(dt)

        if self.waiting:
            self.dot_timer += dt
            if self.dot_timer >= 0.3:
                self.dot_timer -= 0.3
                self.dot_count = (self.dot_count + 1) % 4
            return

        if self.phase == "result" and self.result is not None:
            if input_state.pressed(UP):
                self.scanner_scroll = max(0, getattr(self, "scanner_scroll", 0) - 1)
            elif input_state.pressed(DOWN):
                self.scanner_scroll = getattr(self, "scanner_scroll", 0) + 1
            elif input_state.pressed(A) or input_state.pressed(B):
                self.game.scene_manager.pop()
            return

        if self.phase == "target":
            result = self.target_menu.update(input_state)
            if self.target_menu.cancelled:
                self.game.scene_manager.pop()
                return
            if result is not None:
                choice = self.TARGETS[result]
                if choice == "BACK":
                    self.game.scene_manager.pop()
                elif choice == "CUSTOM":
                    self.game.scene_manager.push(
                        TargetInputScene(
                            self.game,
                            "NMAP",
                            [t for t in self.TARGETS if t not in ("CUSTOM", "BACK")],
                            self._on_custom_target,
                            start_custom=True,
                        )
                    )
                else:
                    self.selected_target = choice
                    self.phase = "scan_type"
                    self.dialog.set_text(f"Target: {choice}. Choose type:")
            return

        if self.phase == "scan_type":
            result = self.scan_menu.update(input_state)
            if self.scan_menu.cancelled:
                self.phase = "target"
                self.dialog.set_text("Select target to scan:")
                return
            if result is not None:
                choice = self.scan_menu.items[result]
                if choice == "BACK":
                    self.phase = "target"
                    self.dialog.set_text("Select target to scan:")
                else:
                    self.selected_scan_type = choice
                    self._start_scan()
            return

    def draw(self, renderer):
        renderer.clear(DARK_BG)
        font = self.game.font
        surface = renderer.get_surface()

        renderer.draw_rect(0, 0, 160, 10, (16, 16, 32))
        font.draw(surface, "[ NMAP TOOL ]", 40, 1, CYAN)

        if self.phase == "target":
            self.target_menu.draw(surface)
        elif self.phase == "scan_type":
            self.scan_menu.draw(surface)
        elif self.phase == "waiting":
            dots = "." * self.dot_count
            font.draw(surface, f"Scanning{dots}", 40, 56, GREEN)
        elif self.phase == "result" and self.result is not None:
            y = 20
            if self.result.success:
                data = self.result.data or {}
                host_count = data.get("host_count", "?")
                font.draw(surface, f"Hosts: {host_count}", 4, y, GREEN)
                y += 10

                command = data.get("command")
                if command:
                    font.draw(surface, f"CMD: {command[:28]}", 4, y, GRAY)
                    y += 10

                for host in data.get("hosts", [])[:5 + getattr(self, "scanner_scroll", 0)]:
                    line = f"{host['ip']} {host['state']}"
                    font.draw(surface, line[:28], 4, y, WHITE)
                    y += 10
                    if y > 88:
                        break

                raw_output = data.get("raw_output", "") or ""
                if raw_output:
                    font.draw(surface, "RAW OUTPUT:", 4, y, GRAY)
                    y += 10
                    for line in raw_output.splitlines()[:2]:
                        font.draw(surface, line[:28], 4, y, WHITE)
                        y += 8

                font.draw(surface, "Use UP/DOWN to scroll", 20, 108, GRAY)
            else:
                font.draw(surface, "Scan failed", 4, y, RED)
                y += 12
                err = str(self.result.error)[:28]
                font.draw(surface, err, 4, y, RED)

        self.dialog.draw(surface)


# ═══════════════════════════════════════════════════════════════════════
#  PET STATUS SCENE — Detailed pet info
# ═══════════════════════════════════════════════════════════════════════
class PetStatusScene(Scene):
    """Full-screen pet status display."""

    def __init__(self, game):
        self.game = game

    def update(self, input_state, dt):
        if input_state.pressed(B) or input_state.pressed(A):
            self.game.scene_manager.pop()

    def draw(self, renderer):
        renderer.clear(DARK_BG)
        pet = self.game.pet
        font = self.game.font
        surface = renderer.get_surface()

        # Header
        renderer.draw_rect(0, 0, 160, 10, (32, 16, 32))
        font.draw(surface, f"[ {pet.name.upper()} STATUS ]", 30, 1, CYAN)

        y = 16
        stats = [
            (f"Name:  {pet.name}", WHITE),
            (f"Stage: {pet.stage.capitalize()}", WHITE),
            (f"Level: {pet.level}", WHITE),
            (f"XP:    {pet.xp}", CYAN),
            (f"Mood:  {pet.mood_name} ({pet.mood:.0f})", 
                GREEN if pet.mood >= 40 else RED),
            (f"Food:  {pet.hunger:.0f}/100",
                GREEN if pet.hunger >= 30 else RED),
            (f"Energy:{pet.energy:.0f}/100",
                GREEN if pet.energy >= 30 else RED),
            ("", WHITE),
            (f"Pings: {pet.total_pings}", GRAY),
            (f"Scans: {pet.total_scans}", GRAY),
            (f"Hosts: {pet.total_hosts_found}", GRAY),
        ]

        for text, color in stats:
            font.draw(surface, text, 8, y, color)
            y += 10

        font.draw(surface, "Press Enter/Esc to go back", 20, 130, GRAY)


# ═══════════════════════════════════════════════════════════════════════
#  GAME OBJECT — Holds shared state
# ═══════════════════════════════════════════════════════════════════════
class Game:
    """Central game object that holds all shared state.

    LEARNING NOTE — dependency injection:
        Instead of global variables, we pass this Game object to each
        scene. Every scene can access game.pet, game.font, etc.
        This is cleaner than globals and easier to test.
    """

    def __init__(self):
        self.renderer = Renderer(scale=4, title="NetGotchi")
        self.input = Input()
        self.scene_manager = SceneManager()
        self.font = PixelFont(size=8)
        self.running = True

        # Load or create pet
        save_data = load_game()
        if save_data and "pet" in save_data:
            self.pet = Pet.from_dict(save_data["pet"])
        else:
            self.pet = Pet("Byte")

    def run(self):
        """Main game loop. This is the heart of the program.

        LEARNING NOTE — the frame loop:
            Every game works the same way at its core:
            1. Process input (what did the player do?)
            2. Update state (what changed in the game world?)
            3. Draw (what does the player see?)
            4. Present (flip the back buffer to the screen)
            5. Wait (cap framerate so we don't burn 100% CPU)

            This loop runs 30 times per second (our target FPS).
            dt (delta time) = seconds since last frame ≈ 0.033s at 30fps.
        """
        # Push the initial scene
        self.scene_manager.push(OverworldScene(self))

        dt = 0.0  # First frame has zero delta
        while self.running:
            # 1. Process input events
            events = pygame.event.get()
            self.input.update(events)

            if self.input.quit_requested:
                self.running = False
                break

            # 2. Update the active scene using dt from last frame
            self.scene_manager.update(self.input, dt)

            # 3. Draw all scenes (bottom to top)
            self.scene_manager.draw(self.renderer)

            # 4. Scale GBC surface to window, display, and get delta time
            # LEARNING NOTE — present() calls clock.tick() internally,
            # which caps FPS and returns the time since last frame.
            dt = self.renderer.present()

            # Check if all scenes popped (shouldn't happen, but safety)
            if self.scene_manager.empty:
                self.running = False

        # Auto-save on exit
        save_game(self.pet)
        pygame.quit()


# ═══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════
# LEARNING NOTE — if __name__ == "__main__":
#   This is Python's "main guard." When you run `python main.py`,
#   Python sets __name__ to "__main__" for that file. But if another
#   file does `import main`, __name__ would be "main" (the module name).
#   The guard ensures the game only starts when you RUN this file,
#   not when you IMPORT it.

if __name__ == "__main__":
    game = Game()
    game.run()
