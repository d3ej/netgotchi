"""
netgotchi.engine.ui
~~~~~~~~~~~~~~~~~~~
JRPG-style UI components: text rendering, dialog boxes, menus, bars.

LEARNING NOTES — this module teaches:
  - pygame.font for rendering text to surfaces
  - Surface caching (don't re-render text every frame!)
  - Building reusable UI components as classes
  - The typewriter text effect (revealing characters over time)
  - How classic JRPG menus work (cursor index + selection)

GBC CONSTRAINT:
    Real GBC uses a built-in 8x8 pixel font baked into hardware. We
    simulate this with pygame's font system using a small size. The text
    is rendered to our 160x144 surface so it stays pixel-perfect.
"""

import pygame
import os

# ── Font path ────────────────────────────────────────────────────────
# LEARNING NOTE — os.path relative to __file__:
#   __file__ is the path of THIS Python file.  We navigate from here
#   to the data/fonts/ directory so the font loads no matter where you
#   run the program from.  This is more robust than a hardcoded path.
_FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "fonts")
FONT_04B03 = os.path.join(_FONT_DIR, "04b03.ttf")

# ── Colors for UI ───────────────────────────────────────────────────────
WHITE = (255, 255, 255)
BLACK = (8, 8, 16)
GRAY = (140, 140, 160)
CYAN = (100, 220, 255)
GREEN = (50, 255, 50)
RED = (255, 80, 80)
YELLOW = (255, 220, 0)
BLUE = (100, 160, 255)

# Box styling
BOX_BG = (16, 16, 32, 220)       # semi-transparent dark
BOX_BORDER = (200, 200, 220)     # light border


class PixelFont:
    """Wrapper around pygame font that renders at GBC-appropriate sizes.

    LEARNING NOTE — font rendering in pygame:
        pygame.font.Font(path, size) loads a font file.
        font.render(text, antialias, color) creates a Surface with the text.
        We use antialias=False for crisp pixel text (no smoothing).

        IMPORTANT: Rendering text creates a NEW surface every call.
        This is slow if done every frame! Cache the result when possible.
    """

    def __init__(self, size=8, bold=False):
        """Initialize with the 04b03 pixel font.

        LEARNING NOTE — 04b03 is a TrueType (.ttf) pixel font:
            Unlike bitmap fonts (like Terminus .otb) which only work at
            specific fixed sizes, TTF fonts scale to ANY size.  04b03 is
            designed for pixel art — its glyphs are crisp grid-aligned
            shapes that look great at small sizes without anti-aliasing.
            At size 8 each glyph is ~5px wide x 8px tall, fitting
            perfectly on our 160x144 GBC surface.

        Args:
            size: Font size in pixels. 8 is the native pixel-perfect size.
            bold: Reserved for future use (04b03 has one weight).
        """
        pygame.font.init()
        self.font = pygame.font.Font(FONT_04B03, size)
        self.size = size
        # Cache rendered text surfaces to avoid re-rendering
        self._cache = {}

    def render(self, text, color=WHITE):
        """Render text to a Surface, using cache when possible.

        LEARNING NOTE — dictionary caching:
            We use (text, color) as a dict key. If we've already rendered
            this exact string in this color, we return the cached surface
            instead of re-rendering. This is a simple but effective
            optimization pattern.

        Args:
            text: String to render.
            color: RGB tuple for text color.

        Returns:
            pygame.Surface with the rendered text.
        """
        cache_key = (text, color)
        if cache_key not in self._cache:
            # antialias=False gives pixel-perfect text
            self._cache[cache_key] = self.font.render(text, False, color)
        return self._cache[cache_key]

    def draw(self, surface, text, x, y, color=WHITE):
        """Render and blit text onto a surface in one call.

        Args:
            surface: Destination pygame.Surface (usually the GBC surface).
            text: String to draw.
            x, y: Position in GBC pixels.
            color: RGB tuple.
        """
        text_surf = self.render(text, color)
        surface.blit(text_surf, (x, y))

    def clear_cache(self):
        """Clear the text cache (useful when changing font settings)."""
        self._cache.clear()


class DialogBox:
    """A JRPG dialog box with typewriter text effect.

    LEARNING NOTES:
        The typewriter effect reveals text one character at a time,
        controlled by a timer. Each frame we check if enough time has
        passed to show the next character.  This is how classic JRPGs
        like Dragon Quest and Pokemon display dialog text.

    Usage:
        dialog = DialogBox(font)
        dialog.set_text("A wild packet appeared!")
        # In game loop:
        dialog.update(dt)
        dialog.draw(renderer.get_surface())
    """

    def __init__(self, font, x=4, y=104, width=152, height=36):
        self.font = font
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self._full_text = ""
        self._visible_chars = 0
        self._char_timer = 0.0
        self._chars_per_second = 30  # Speed of typewriter effect
        self._finished = True

    def set_text(self, text):
        """Set new text and restart the typewriter effect."""
        self._full_text = text
        self._visible_chars = 0
        self._char_timer = 0.0
        self._finished = False

    def update(self, dt):
        """Advance the typewriter effect.

        LEARNING NOTE — delta time (dt):
            dt is the time in seconds since last frame. By accumulating
            dt into a timer, we can trigger events at a consistent rate
            regardless of frame rate.  This is fundamental to game dev!

        Args:
            dt: Seconds since last frame.
        """
        if self._finished:
            return

        self._char_timer += dt
        chars_to_show = int(self._char_timer * self._chars_per_second)

        if chars_to_show > self._visible_chars:
            self._visible_chars = min(chars_to_show, len(self._full_text))

        if self._visible_chars >= len(self._full_text):
            self._finished = True

    def skip(self):
        """Instantly show all text (when player presses Enter)."""
        self._visible_chars = len(self._full_text)
        self._finished = True

    @property
    def finished(self):
        return self._finished

    def draw(self, surface):
        """Draw the dialog box and visible text.

        Args:
            surface: The GBC-resolution pygame.Surface.
        """
        # Draw semi-transparent background
        box_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        box_surf.fill(BOX_BG)
        surface.blit(box_surf, (self.x, self.y))

        # Draw border
        pygame.draw.rect(surface, BOX_BORDER,
                         (self.x, self.y, self.width, self.height), 1)

        # Draw visible portion of text (word-wrapped)
        visible_text = self._full_text[:self._visible_chars]
        self._draw_wrapped_text(surface, visible_text)

    def _draw_wrapped_text(self, surface, text):
        """Simple word-wrap text drawing.

        LEARNING NOTE — font.size() for accurate measurement:
            Instead of guessing character widths, we ask the font how
            wide a string actually is in pixels. font.font.size(text)
            returns (width, height).  This works correctly for both
            fixed-width fonts like Terminus AND proportional fonts.
        """
        words = text.split(" ")
        lines = []
        current_line = ""
        max_width = self.width - 8  # padding on each side

        for word in words:
            test_line = current_line + " " + word if current_line else word
            text_w, _ = self.font.font.size(test_line)
            if text_w > max_width and current_line:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)

        line_height = self.font.size + 2
        max_lines = max(1, (self.height - 8) // line_height)
        for i, line in enumerate(lines[:max_lines]):
            self.font.draw(surface, line,
                           self.x + 4, self.y + 4 + i * line_height, WHITE)


class Menu:
    """A JRPG cursor-based menu (like Dragon Quest's command menu).

    LEARNING NOTES:
        Classic JRPG menus work like this:
        1. Show a list of options in a box
        2. A cursor (▸) highlights the current selection
        3. Up/Down moves the cursor
        4. Enter confirms, Escape cancels

        The cursor index is just an integer that wraps around:
        pressing Down at the bottom goes back to top.

    Usage:
        menu = Menu(font, ["TOOLS", "PET", "QUESTS", "STATUS", "SAVE"])
        # In update:
        result = menu.update(input_state)
        if result is not None:
            print(f"Selected: {menu.items[result]}")
    """

    def __init__(self, font, items, x=4, y=4, width=60):
        self.font = font
        self.items = items
        self.x = x
        self.y = y
        self.width = width
        self.cursor = 0
        self._cancelled = False

    def update(self, input_state):
        """Handle cursor movement and selection.

        LEARNING NOTE — modulo wrapping:
            self.cursor % len(self.items) makes the cursor wrap around.
            If cursor goes to 5 with 5 items, 5 % 5 = 0 → back to top.
            If cursor goes to -1, in Python -1 % 5 = 4 → bottom item.

        Args:
            input_state: The Input object.

        Returns:
            Index of selected item (int) if A pressed, or None.
        """
        from .input import UP, DOWN, A, B

        self._cancelled = False

        if input_state.pressed(DOWN):
            self.cursor = (self.cursor + 1) % len(self.items)
        elif input_state.pressed(UP):
            self.cursor = (self.cursor - 1) % len(self.items)
        elif input_state.pressed(A):
            return self.cursor
        elif input_state.pressed(B):
            self._cancelled = True
            return None

        return None

    @property
    def cancelled(self):
        return self._cancelled

    def draw(self, surface):
        """Draw the menu box with cursor and items.

        Args:
            surface: GBC pygame.Surface.
        """
        item_height = self.font.size + 2
        height = len(self.items) * item_height + 8

        # Background
        box_surf = pygame.Surface((self.width, height), pygame.SRCALPHA)
        box_surf.fill(BOX_BG)
        surface.blit(box_surf, (self.x, self.y))

        # Border
        pygame.draw.rect(surface, BOX_BORDER,
                         (self.x, self.y, self.width, height), 1)

        # Items with cursor
        for i, item in enumerate(self.items):
            ix = self.x + 12
            iy = self.y + 4 + i * item_height
            color = WHITE if i == self.cursor else GRAY

            # Draw cursor arrow for selected item
            if i == self.cursor:
                self.font.draw(surface, ">", self.x + 4, iy, CYAN)

            self.font.draw(surface, item, ix, iy, color)


class StatusBar:
    """A small HP/XP-style bar with label.

    LEARNING NOTE — progress bars:
        A bar is just two rectangles: a background (empty) and a
        foreground (filled) whose width is proportional to the value.
        width_filled = int(total_width * (current / maximum))
    """

    def __init__(self, x, y, width, height=4,
                 bg_color=(40, 40, 60), fg_color=GREEN):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.fg_color = fg_color

    def draw(self, surface, current, maximum):
        """Draw the bar at current/maximum fill level.

        Args:
            surface: pygame.Surface to draw on.
            current: Current value (e.g., current HP).
            maximum: Maximum value (e.g., max HP).
        """
        # Background bar
        pygame.draw.rect(surface, self.bg_color,
                         (self.x, self.y, self.width, self.height))
        # Filled portion
        if maximum > 0:
            fill_w = int(self.width * (current / maximum))
            fill_w = max(0, min(fill_w, self.width))  # clamp
            if fill_w > 0:
                pygame.draw.rect(surface, self.fg_color,
                                 (self.x, self.y, fill_w, self.height))
