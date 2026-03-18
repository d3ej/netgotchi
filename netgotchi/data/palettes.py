"""
netgotchi.engine.palettes
~~~~~~~~~~~~~~~~~~~~~~~~~
GBC-inspired color palettes. On the real Game Boy Color, each sprite/tile
can use at most 4 colors (from a pool of 32,768). We keep that spirit by
defining named 4-color palettes. Each palette is a tuple of 4 RGBA tuples,
indexed 0-3 where 0 is usually transparent or darkest.

LEARNING NOTE — tuples vs lists:
    We use tuples here because palettes are IMMUTABLE data. Python tuples
    are slightly faster to access and signal "this shouldn't change."
    Lists would work too, but tuples are the right tool for fixed data.
"""

# ── GBC-authentic grays (original DMG look) ─────────────────────────────
DMG = (
    (15,   56,  15, 255),   # darkest green-black
    (48,   98,  48, 255),   # dark green
    (139, 172,  15, 255),   # light green
    (155, 188,  15, 255),   # lightest green
)

# ── UI palettes ─────────────────────────────────────────────────────────
UI_DEFAULT = (
    (8,    8,   16, 255),   # near-black background
    (48,   48,  72, 255),   # dark border
    (200, 200, 220, 255),   # light text
    (255, 255, 255, 255),   # bright white
)

UI_HEALTH_GREEN = (
    (8,    8,   16, 255),
    (0,   80,    0, 255),   # dark green
    (0,  180,    0, 255),   # mid green
    (50, 255,   50, 255),   # bright green
)

UI_HEALTH_RED = (
    (8,    8,   16, 255),
    (80,   0,    0, 255),
    (180,  0,    0, 255),
    (255, 50,   50, 255),
)

UI_XP_BLUE = (
    (8,    8,   16, 255),
    (0,    0,  100, 255),
    (40,  80,  200, 255),
    (100, 160, 255, 255),
)

# ── Pet palettes (one per evolution stage) ──────────────────────────────
PET_EGG = (
    (0,    0,    0,   0),   # transparent
    (180, 180, 170, 255),   # eggshell
    (220, 215, 200, 255),   # light shell
    (140, 135, 120, 255),   # crack shadow
)

PET_HATCHLING = (
    (0,    0,    0,   0),
    (55,  80,  165, 255),   # body blue (borrowed from your player sprite!)
    (100, 140, 220, 255),   # light blue
    (30,  48,  100, 255),   # dark blue
)

PET_JUVENILE = (
    (0,    0,    0,   0),
    (80,  55,  165, 255),   # purple body
    (140, 100, 220, 255),   # light purple
    (48,  30,  100, 255),   # dark purple
)

# ── Network tool palettes ───────────────────────────────────────────────
TOOL_PING = (
    (8,    8,   16, 255),
    (0,  200,  100, 255),   # green for success
    (200,  50,   0, 255),   # red for failure
    (255, 220,   0, 255),   # yellow for in-progress
)

TOOL_NMAP = (
    (8,    8,   16, 255),
    (100, 200, 255, 255),   # cyan: open port
    (200, 100, 100, 255),   # muted red: closed
    (100, 100, 100, 255),   # gray: filtered
)

TOOL_SSH = (
    (8,    8,   16, 255),
    (0,  255,    0, 255),   # "terminal green"
    (0,  170,    0, 255),   # mid green
    (0,  100,    0, 255),   # dim green
)


def get_color(palette, index):
    """Safely get a color from a palette by index.

    LEARNING NOTE — bounds checking:
        Rather than letting Python raise an IndexError, we clamp to valid
        range. This is defensive coding at a SYSTEM BOUNDARY (palette data
        could come from sprite files). Internal code doesn't need this.

    Args:
        palette: A tuple of 4 RGBA color tuples.
        index: 0-3 palette index.

    Returns:
        RGBA tuple (r, g, b, a).
    """
    return palette[max(0, min(index, len(palette) - 1))]
