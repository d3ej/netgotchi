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

import pygame
import sys

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
from netgotchi.tools.ssh import SSHTool
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

        # A button skips dialog text
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

        # B button closes menu
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

    TOOLS = ["PING", "SSH", "BACK"]

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
    TARGETS = ["8.8.8.8", "1.1.1.1", "127.0.0.1", "BACK"]

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
            else:
                # Start ping!
                self.waiting = True
                self.result = None
                self.dialog.set_text(f"Pinging {choice}...")
                self.ping_tool.run(
                    {"target": choice, "count": 4},
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

            rtt = data.get("avg_rtt_ms", "?")
            font.draw(surface, f"RTT: {rtt}ms", 4, y, WHITE)
            y += 10

            loss = data.get("packet_loss_pct", "?")
            loss_color = GREEN if loss == 0 else RED
            font.draw(surface, f"Loss: {loss}%", 4, y, loss_color)
            y += 10

            font.draw(surface, f"+{self.result.xp_reward} XP", 4, y, CYAN)
            y += 14

            font.draw(surface, f"Time: {self.result.duration:.1f}s", 4, y, GRAY)
        else:
            font.draw(surface, "PING FAILED!", 4, y, RED)
            y += 12
            err = str(self.result.error)[:25]
            font.draw(surface, err, 4, y, RED)

        font.draw(surface, "Press A/B to continue", 20, 92, GRAY)


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
        host_labels = [h["name"] for h in self._hosts] + ["BACK"]
        self.host_menu = Menu(game.font, host_labels, x=4, y=24, width=90)
        self.cmd_menu = Menu(game.font, self.COMMANDS, x=4, y=24, width=80)
        self.dialog = DialogBox(game.font, x=4, y=104, width=152, height=36)
        self.dialog.set_text("Select SSH target:")

        self.selected_host = None  # Will be a dict from discover_hosts()
        self.selected_cmd = None
        self.dot_timer = 0.0
        self.dot_count = 0
        self.scroll_offset = 0  # For scrolling long output

        # CLI typing state
        self._cli_buffer = ""       # What the user has typed so far
        self._cursor_timer = 0.0    # Timer for blinking cursor
        self._cursor_visible = True # Cursor blink state

    def _on_ssh_done(self, result):
        """Callback from SSH worker thread."""
        self.result = result
        self.waiting = False

    def on_exit(self):
        """Clean up when leaving the SSH scene."""
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
                if result >= len(self._hosts):
                    # "BACK" selected
                    self.game.scene_manager.pop()
                else:
                    self.selected_host = self._hosts[result]
                    display = self.selected_host["name"]
                    self.phase = "command"
                    self.dialog.set_text(f"Run on {display}:")
            return

        # ── CLI typing phase ─────────────────────────────────────────
        # LEARNING NOTE — text input in pygame:
        #   We use pygame.TEXTINPUT events (stored in input_state.text_events)
        #   to capture what the user types. This handles shift, keyboard
        #   layout, etc. automatically. KEYDOWN is only used for control
        #   keys: backspace to delete, enter to submit, escape to cancel.
        if self.phase == "cli":
            # Process typed characters
            for char in input_state.text_events:
                if len(self._cli_buffer) < 60:  # Max command length
                    self._cli_buffer += char

            # Process control keys from raw KEYDOWN events
            for event in input_state.key_events:
                if event.key == pygame.K_BACKSPACE:
                    self._cli_buffer = self._cli_buffer[:-1]
                elif event.key == pygame.K_RETURN:
                    if self._cli_buffer.strip():
                        self._submit_cli_command()
                    return
                elif event.key == pygame.K_ESCAPE:
                    pygame.key.set_repeat(0)  # Restore normal input
                    self._cli_buffer = ""
                    self.phase = "command"
                    self.dialog.set_text(f"Run on {self.selected_host['name']}:")
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
                    # LEARNING NOTE — pygame.key.set_repeat():
                    #   Enables key repeat when held down. The first
                    #   arg is the delay (ms) before repeat starts,
                    #   the second is the interval (ms) between repeats.
                    #   This makes backspace feel natural when held.
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

        font.draw(surface, "Press A/B to continue", 20, 100, GRAY)


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

        font.draw(surface, "Press A/B to go back", 20, 130, GRAY)


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
