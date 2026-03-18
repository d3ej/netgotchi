"""
netgotchi.engine.renderer
~~~~~~~~~~~~~~~~~~~~~~~~~
GBC-constrained pixel renderer. Draws to a small 160x144 surface (the
actual Game Boy Color resolution), then scales it up to your window.

LEARNING NOTES sprinkled throughout — this module teaches:
  - pygame.Surface basics (creating, blitting, scaling)
  - Integer scaling for crisp pixel art (no blurry bilinear filtering)
  - The "virtual resolution" pattern used in retro-style games
  - How to draw rectangles and individual "fat pixels"
"""

import pygame

# ── Constants ───────────────────────────────────────────────────────────
# Game Boy Color native resolution
GBC_WIDTH = 160
GBC_HEIGHT = 144

# How many times to scale up the tiny surface for the window.
# 4x means a 640x576 window.  You can change this!
DEFAULT_SCALE = 4

# Background color — very dark blue-black, like a GBC screen
BG_COLOR = (8, 8, 16)


class Renderer:
    """Manages a GBC-resolution surface and scales it to the display.

    LEARNING NOTE — the two-surface pattern:
        self._surface  = the tiny 160x144 canvas you draw on
        self._display  = the big window the player actually sees

        Everything is drawn to _surface first, then at the end of each
        frame we scale _surface up to _display.  This gives us
        perfectly crisp pixel art at any window size.

    Usage:
        renderer = Renderer(scale=4)
        # ... each frame ...
        renderer.clear()
        renderer.draw_pixel(10, 20, (255, 0, 0))
        renderer.present()
    """

    def __init__(self, scale=DEFAULT_SCALE, title="NetGotchi"):
        """Initialize pygame, create window and internal surface.

        Args:
            scale: Integer multiplier for the window size.
            title: Window title bar text.
        """
        # LEARNING NOTE — pygame.init():
        #   Initializes ALL pygame subsystems (display, audio, fonts, etc).
        #   Always call this before doing anything with pygame.
        pygame.init()

        self.scale = scale
        self.width = GBC_WIDTH
        self.height = GBC_HEIGHT

        # Create the actual OS window (the big one the player sees)
        window_w = self.width * scale
        window_h = self.height * scale
        self._display = pygame.display.set_mode((window_w, window_h))
        pygame.display.set_caption(title)

        # Create the tiny GBC-sized surface we actually draw to.
        # LEARNING NOTE — Surface vs display:
        #   pygame.Surface is just an image in memory. It's not shown
        #   on screen until you "blit" (copy) it onto the display surface.
        self._surface = pygame.Surface((self.width, self.height))

        # We'll track FPS with a Clock
        self.clock = pygame.time.Clock()
        self.fps = 30  # GBC ran at ~59.7 fps, but 30 is fine for a tool

    def clear(self, color=BG_COLOR):
        """Fill the GBC surface with a solid color (default: dark).

        LEARNING NOTE — fill():
            Surface.fill(color) paints every pixel on that surface.
            We do this at the start of each frame to erase the last frame.
        """
        self._surface.fill(color)

    def draw_pixel(self, x, y, color):
        """Draw a single 'fat pixel' at GBC coordinates.

        LEARNING NOTE — coordinate system:
            (0, 0) is the top-left corner.
            x goes right (0-159), y goes down (0-143).
            Each pixel here = one GBC pixel = 4×4 screen pixels at scale 4.

        Args:
            x: Horizontal position (0 to 159).
            y: Vertical position (0 to 143).
            color: (R, G, B) or (R, G, B, A) tuple.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self._surface.set_at((x, y), color)

    def draw_rect(self, x, y, w, h, color):
        """Draw a filled rectangle on the GBC surface.

        Args:
            x, y: Top-left corner in GBC coordinates.
            w, h: Width and height in GBC pixels.
            color: (R, G, B) tuple.
        """
        pygame.draw.rect(self._surface, color, (x, y, w, h))

    def draw_rect_outline(self, x, y, w, h, color, thickness=1):
        """Draw an outlined (unfilled) rectangle.

        LEARNING NOTE — the last argument to pygame.draw.rect():
            When you pass a width > 0, it draws only the border, not filled.
        """
        pygame.draw.rect(self._surface, color, (x, y, w, h), thickness)

    def draw_sprite(self, sprite_data, palette, x, y, px_size=1):
        """Draw a sprite from a 2D array of palette indices.

        This is ported from your SDL2 project's draw_sprite_at() function!
        Each value in sprite_data is a palette index (0 = transparent).

        LEARNING NOTE — nested loops:
            We loop row-by-row, column-by-column through the sprite grid.
            For each non-zero cell, we look up its color in the palette
            and draw a filled rectangle of size px_size × px_size.

        Args:
            sprite_data: List of lists (2D grid), each cell is 0-3.
            palette: Tuple of 4 color tuples (index 0 = transparent).
            x, y: Top-left position on GBC surface.
            px_size: How many GBC pixels per sprite pixel (1 = 1:1).
        """
        for row_idx, row in enumerate(sprite_data):
            for col_idx, pal_index in enumerate(row):
                if pal_index == 0:
                    continue  # 0 = transparent, skip
                color = palette[pal_index]
                draw_x = x + col_idx * px_size
                draw_y = y + row_idx * px_size
                if px_size == 1:
                    self.draw_pixel(draw_x, draw_y, color)
                else:
                    self.draw_rect(draw_x, draw_y, px_size, px_size, color)

    def blit(self, surface, pos=(0, 0)):
        """Copy another Surface onto the GBC surface.

        LEARNING NOTE — blit():
            'blit' means 'block image transfer' — it copies pixels from
            one surface onto another. This is how you draw images, text,
            or pre-rendered UI elements onto the screen.

        Args:
            surface: A pygame.Surface to draw.
            pos: (x, y) position on the GBC surface.
        """
        self._surface.blit(surface, pos)

    def present(self):
        """Scale the GBC surface up and show it on screen.

        LEARNING NOTE — pygame.transform.scale():
            This takes our tiny 160x144 surface and stretches it to fill
            the window.  Because we use integer scaling (4x), each GBC
            pixel maps to exactly 4×4 screen pixels = crisp pixel art.

            If you used non-integer scaling (like 3.5x) you'd get ugly
            blurry pixels.  Always use integer scaling for retro games.
        """
        # Scale small surface → big display
        scaled = pygame.transform.scale(
            self._surface,
            (self.width * self.scale, self.height * self.scale)
        )
        self._display.blit(scaled, (0, 0))

        # LEARNING NOTE — flip():
        #   pygame uses double buffering. You draw to a back buffer,
        #   then flip() swaps it to the visible screen. This prevents
        #   tearing/flickering.
        pygame.display.flip()

        # Cap the frame rate and return delta time in seconds.
        # LEARNING NOTE — tick() returns ms since last call AND caps FPS.
        # We return seconds (ms / 1000) so game logic uses clean units.
        return self.clock.tick(self.fps) / 1000.0

    def get_surface(self):
        """Get the raw GBC surface for direct drawing."""
        return self._surface
