"""
netgotchi.engine.scene
~~~~~~~~~~~~~~~~~~~~~~
Stack-based scene manager for switching between game screens.

LEARNING NOTES — this module teaches:
  - The State pattern (each screen is an independent object)
  - Stack data structures (push/pop) for layered UIs
  - Abstract base classes vs duck typing in Python
  - Why games use scene managers instead of giant if/elif blocks

HOW IT WORKS:
    Imagine a stack of transparent sheets. The scene on TOP is the one
    that gets drawn and receives input. When you open a menu, you PUSH
    a new scene on top of the overworld. When you close it, you POP it
    off and the overworld is back on top.

    Stack: [Overworld] → push Menu → [Overworld, Menu]
                       → push Dialog → [Overworld, Menu, Dialog]
                       → pop → [Overworld, Menu]
                       → pop → [Overworld]
"""


class Scene:
    """Base class for all game scenes. Subclass this for each screen.

    LEARNING NOTE — duck typing:
        Python doesn't require you to inherit from a base class to make
        things work. If your class has update() and draw() methods,
        the scene manager will happily call them. This base class is
        here for documentation and to provide default no-op methods.
    """

    def on_enter(self):
        """Called when this scene becomes the active (top) scene."""
        pass

    def on_exit(self):
        """Called when this scene is removed from the stack."""
        pass

    def on_pause(self):
        """Called when another scene is pushed on top of this one."""
        pass

    def on_resume(self):
        """Called when the scene above is popped, making this active again."""
        pass

    def update(self, input_state, dt):
        """Update game logic for this scene.

        Args:
            input_state: The Input object with current button states.
            dt: Delta time in seconds since last frame.
        """
        pass

    def draw(self, renderer):
        """Draw this scene to the renderer.

        Args:
            renderer: The Renderer object to draw on.
        """
        pass


class SceneManager:
    """Manages a stack of Scene objects.

    LEARNING NOTE — list as stack:
        Python lists work as stacks using .append() for push and .pop()
        for pop. The last element (index -1) is the "top" of the stack.
    """

    def __init__(self):
        self._stack = []

    def push(self, scene):
        """Push a new scene on top of the stack.

        The current top scene gets paused, the new scene gets entered.
        """
        if self._stack:
            self._stack[-1].on_pause()
        self._stack.append(scene)
        scene.on_enter()

    def pop(self):
        """Remove the top scene and resume the one below.

        Returns:
            The scene that was removed, or None if stack was empty.
        """
        if not self._stack:
            return None
        scene = self._stack.pop()
        scene.on_exit()
        if self._stack:
            self._stack[-1].on_resume()
        return scene

    def replace(self, scene):
        """Replace the top scene with a new one.

        Useful for transitions like: title screen → overworld
        (you don't want the title screen lurking underneath).
        """
        if self._stack:
            self._stack[-1].on_exit()
            self._stack[-1] = scene
        else:
            self._stack.append(scene)
        scene.on_enter()

    def update(self, input_state, dt):
        """Update only the top scene."""
        if self._stack:
            self._stack[-1].update(input_state, dt)

    def draw(self, renderer):
        """Draw all scenes bottom-to-top (for transparency effects).

        LEARNING NOTE — drawing order:
            We draw ALL scenes, not just the top one. This lets you have
            a semi-transparent menu overlaying the game world. Scenes
            at the bottom are drawn first, scenes on top are drawn last
            (painter's algorithm — just like your SDL2 dungeon game!).
        """
        for scene in self._stack:
            scene.draw(renderer)

    @property
    def current(self):
        """The currently active (top) scene, or None."""
        return self._stack[-1] if self._stack else None

    @property
    def empty(self):
        return len(self._stack) == 0
