"""
netgotchi.engine.input
~~~~~~~~~~~~~~~~~~~~~~
Maps keyboard (and optional gamepad) to virtual GBC buttons.

LEARNING NOTES — this module teaches:
  - pygame event handling (event queue, KEYDOWN/KEYUP)
  - The "virtual button" abstraction pattern
  - Why games decouple physical keys from game actions
  - Dictionary lookups as a cleaner alternative to long if/elif chains

DESIGN NOTE:
    Real GBC has 8 buttons: D-pad (Up/Down/Left/Right), A, B, Start, Select.
    We map keyboard keys to these virtual buttons. This means the rest of
    the code never cares which physical key was pressed — it just checks
    "was the A button pressed?"  This makes it trivial to add gamepad
    support later.
"""

import pygame

# ── Virtual button names ────────────────────────────────────────────────
# These are just strings used as dictionary keys.
UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"
A = "a"          # Confirm / interact
B = "b"          # Cancel / back
START = "start"  # Open menu
SELECT = "select"  # Secondary action

# ── Default key bindings ────────────────────────────────────────────────
# LEARNING NOTE — dictionary mapping:
#   Instead of writing a big if/elif chain, we map pygame key constants
#   to our virtual button names.  To look up what button a key maps to,
#   we just do:  button = DEFAULT_KEYS.get(key, None)
#   If the key isn't in the dict, we get None.
DEFAULT_KEYS = {
    pygame.K_UP:     UP,
    pygame.K_DOWN:   DOWN,
    pygame.K_LEFT:   LEFT,
    pygame.K_RIGHT:  RIGHT,
    pygame.K_w:      UP,
    pygame.K_s:      DOWN,
    pygame.K_a:      LEFT,
    pygame.K_d:      RIGHT,
    pygame.K_RETURN: A,
    pygame.K_z:      A,
    pygame.K_ESCAPE: B,
    pygame.K_x:      B,
    pygame.K_SPACE:  START,
    pygame.K_TAB:    SELECT,
}


class Input:
    """Tracks virtual button state each frame.

    LEARNING NOTE — "pressed" vs "held":
        'pressed' = the button went DOWN this exact frame (edge trigger).
        'held'    = the button is currently down (level trigger).

        This distinction matters! A menu cursor should move once per
        press, not fly through every option while you hold the key.

    Usage:
        inp = Input()
        # In your game loop:
        inp.update(pygame_events)
        if inp.pressed(A):
            do_confirm()
        if inp.held(UP):
            move_character()
    """

    def __init__(self, key_map=None):
        self._key_map = key_map or DEFAULT_KEYS
        self._pressed = set()   # Buttons pressed THIS frame
        self._held = set()      # Buttons currently held down
        self._released = set()  # Buttons released THIS frame
        self.quit_requested = False

        # LEARNING NOTE — text input events:
        #   pygame.TEXTINPUT gives you the actual characters the OS
        #   resolved (handling shift, keyboard layout, etc.).
        #   We store the raw events each frame so scenes that need
        #   typed text (like an SSH CLI) can read them directly.
        self.text_events = []    # List of characters typed this frame
        self.key_events = []     # Raw KEYDOWN events (for backspace, etc.)

    def update(self, events):
        """Process pygame events for the current frame.

        LEARNING NOTE — the event queue:
            pygame collects all OS events (keyboard, mouse, window, etc.)
            into a queue. You MUST process this queue every frame, or
            your app will appear frozen to the OS.

            We iterate through events and sort them into our button sets.

        Args:
            events: List from pygame.event.get()
        """
        # Clear per-frame sets
        self._pressed.clear()
        self._released.clear()
        self.text_events.clear()
        self.key_events.clear()

        for event in events:
            if event.type == pygame.QUIT:
                self.quit_requested = True

            elif event.type == pygame.TEXTINPUT:
                # LEARNING NOTE — TEXTINPUT vs KEYDOWN:
                #   TEXTINPUT gives you the resolved character (e.g. "A"
                #   when shift+a is pressed). KEYDOWN gives the raw key
                #   code. Use TEXTINPUT for actual text, KEYDOWN for
                #   control keys like backspace, enter, arrows.
                self.text_events.append(event.text)

            elif event.type == pygame.KEYDOWN:
                self.key_events.append(event)
                button = self._key_map.get(event.key)
                if button:
                    self._pressed.add(button)
                    self._held.add(button)

            elif event.type == pygame.KEYUP:
                button = self._key_map.get(event.key)
                if button:
                    self._held.discard(button)
                    self._released.add(button)

    def pressed(self, button):
        """True if button was JUST pressed this frame."""
        return button in self._pressed

    def held(self, button):
        """True if button is currently held down."""
        return button in self._held

    def released(self, button):
        """True if button was JUST released this frame."""
        return button in self._released

    def any_pressed(self):
        """True if ANY button was pressed this frame.

        LEARNING NOTE — bool() on collections:
            In Python, empty sets/lists/dicts are 'falsy',
            non-empty ones are 'truthy'. So `bool(self._pressed)`
            is True if any button was pressed.
        """
        return bool(self._pressed)
