"""
netgotchi.pet.sprites
~~~~~~~~~~~~~~~~~~~~~
Pixel-art sprite data for the pet at each evolution stage.

LEARNING NOTES — this module teaches:
  - 2D lists (lists of lists) as sprite grids
  - How palette-indexed sprites work (just like your SDL2 project!)
  - The sprite-sheet concept adapted to code-defined art

HOW SPRITE DATA WORKS:
    Each sprite is an 8x8 grid (list of 8 lists, each with 8 integers).
    Each integer is a palette index:
        0 = transparent (don't draw)
        1 = palette color 1
        2 = palette color 2
        3 = palette color 3

    The Renderer.draw_sprite() method reads these grids and draws
    colored rectangles, exactly like draw_sprite_at() in your C project.

    To make bigger sprites, we can either:
    - Use larger grids (16x16)
    - Draw at px_size=2 to make each "pixel" 2x2 GBC pixels
"""

# ═══════════════════════════════════════════════════════════════════════
# EGG — simple oval shape, slight crack detail
# ═══════════════════════════════════════════════════════════════════════
EGG_IDLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 1, 2, 2, 1, 0, 0],
    [0, 1, 2, 2, 3, 2, 1, 0],
    [0, 1, 2, 3, 2, 2, 1, 0],
    [0, 1, 2, 2, 2, 2, 1, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

EGG_WOBBLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 0, 0],
    [0, 0, 0, 1, 2, 2, 1, 0],
    [0, 0, 1, 2, 2, 3, 2, 0],
    [0, 0, 1, 2, 3, 2, 2, 0],
    [0, 0, 1, 2, 2, 2, 1, 0],
    [0, 0, 0, 1, 1, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

# ═══════════════════════════════════════════════════════════════════════
# HATCHLING — small creature with eyes, inspired by early Tamagotchi
# ═══════════════════════════════════════════════════════════════════════
HATCHLING_IDLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 2, 1, 1, 2, 1, 0],
    [0, 1, 3, 2, 2, 3, 1, 0],
    [0, 0, 1, 2, 2, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

HATCHLING_HAPPY = [
    [0, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 2, 1, 1, 2, 1, 0],
    [0, 1, 3, 2, 2, 3, 1, 0],
    [0, 0, 1, 3, 3, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

HATCHLING_SAD = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 3, 1, 1, 3, 1, 0],
    [0, 1, 2, 2, 2, 2, 1, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

# ═══════════════════════════════════════════════════════════════════════
# JUVENILE — larger creature, more detail, antenna/features
# ═══════════════════════════════════════════════════════════════════════
JUVENILE_IDLE = [
    [0, 1, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 3, 2, 2, 3, 1, 0],
    [0, 1, 2, 2, 2, 2, 1, 0],
    [0, 1, 2, 3, 3, 2, 1, 0],
    [0, 0, 1, 2, 2, 1, 0, 0],
    [0, 1, 1, 0, 0, 1, 1, 0],
    [0, 1, 0, 0, 0, 0, 1, 0],
]

JUVENILE_HAPPY = [
    [1, 0, 0, 0, 0, 0, 0, 1],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 3, 2, 2, 3, 1, 0],
    [0, 1, 2, 2, 2, 2, 1, 0],
    [0, 1, 2, 3, 3, 2, 1, 0],
    [0, 0, 1, 2, 2, 1, 0, 0],
    [0, 1, 0, 0, 0, 0, 1, 0],
    [1, 0, 0, 0, 0, 0, 0, 1],
]

# ═══════════════════════════════════════════════════════════════════════
# Sprite lookup tables
# ═══════════════════════════════════════════════════════════════════════
# LEARNING NOTE — dictionary of dictionaries:
#   SPRITES[stage][animation_name] → sprite data grid
#   This makes it easy to look up the right sprite:
#     sprite = SPRITES[pet.stage]["idle"]

SPRITES = {
    "egg": {
        "idle": EGG_IDLE,
        "happy": EGG_WOBBLE,
        "sad": EGG_IDLE,
        "wobble": EGG_WOBBLE,
    },
    "hatchling": {
        "idle": HATCHLING_IDLE,
        "happy": HATCHLING_HAPPY,
        "sad": HATCHLING_SAD,
    },
    "juvenile": {
        "idle": JUVENILE_IDLE,
        "happy": JUVENILE_HAPPY,
        "sad": JUVENILE_IDLE,
    },
}


def get_sprite(stage, animation="idle"):
    """Get sprite data for a given stage and animation.

    LEARNING NOTE — chained .get() with defaults:
        This safely handles missing stages or animations by falling
        back to known-good defaults. Defensive at system boundary
        (sprite data could be modified/extended later).

    Args:
        stage: Evolution stage string (e.g., "hatchling").
        animation: Animation name (e.g., "idle", "happy", "sad").

    Returns:
        2D list of palette indices.
    """
    stage_sprites = SPRITES.get(stage, SPRITES["egg"])
    return stage_sprites.get(animation, stage_sprites.get("idle", EGG_IDLE))
