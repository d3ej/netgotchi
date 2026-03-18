"""
netgotchi.tools.base
~~~~~~~~~~~~~~~~~~~~
Base class for all network tools. Each tool runs in a background thread
so the UI doesn't freeze during network operations.

LEARNING NOTES — this module teaches:
  - Python threading (background tasks)
  - Abstract base classes (designing interfaces)
  - The Observer pattern (posting events when work completes)
  - Thread safety basics (why you can't update UI from a thread)

WHY THREADS?
    Network operations (ping, scan, SSH) can take seconds or even minutes.
    If we ran them in the main thread, the game loop would stop — no
    drawing, no input processing, the window would freeze.

    Instead, we run tools in a BACKGROUND THREAD. The game loop continues
    normally while the tool works. When it's done, it posts a result
    back via a callback or pygame event.

    ┌─────────────┐     ┌──────────────────┐
    │ Main Thread  │     │ Worker Thread     │
    │ (game loop)  │     │ (network tool)    │
    │              │     │                   │
    │  draw()      │     │  execute()        │
    │  update()    │     │  ...scanning...   │
    │  draw()      │     │  ...scanning...   │
    │  update()    │     │  done! → callback │
    └─────────────┘     └──────────────────┘
"""

import threading
import time


class ToolResult:
    """Container for a tool's execution result.

    LEARNING NOTE — data classes:
        This is a simple container for data. In Python 3.7+ you could
        use @dataclass for this, but a plain class is clearer for learning.
        The key idea: separate the RESULT from the TOOL that created it.
    """

    def __init__(self, tool_name, success, data=None, error=None,
                 duration=0.0, xp_reward=0):
        self.tool_name = tool_name
        self.success = success
        self.data = data or {}     # Tool-specific result data
        self.error = error         # Error message if failed
        self.duration = duration   # How long it took (seconds)
        self.xp_reward = xp_reward


class BaseTool:
    """Abstract base for all network tools.

    LEARNING NOTES:
        Subclasses MUST implement:
          - name (property): Tool's display name
          - _execute(params): The actual network operation

        Subclasses CAN override:
          - xp_reward(result): How much XP this tool awards
          - food_value(result): How much it feeds the pet

    Usage:
        class PingTool(BaseTool):
            @property
            def name(self):
                return "Ping"

            def _execute(self, params):
                # ... do the ping ...
                return {"rtt_ms": 12.5, "success": True}

        ping = PingTool()
        ping.run({"target": "8.8.8.8"}, callback=on_ping_done)
    """

    def __init__(self):
        self._running = False
        self._thread = None

    @property
    def name(self):
        """Display name for this tool. Override in subclass."""
        return "Unknown Tool"

    @property
    def running(self):
        """True if the tool is currently executing."""
        return self._running

    def run(self, params, callback=None):
        """Run the tool in a background thread.

        LEARNING NOTE — threading.Thread:
            threading.Thread(target=fn, args=(...)) creates a new thread.
            .start() begins execution. The function runs in parallel with
            your main code. Use daemon=True so the thread dies when the
            main program exits (otherwise it could keep running forever).

        Args:
            params: Dict of parameters (e.g., {"target": "10.0.0.1"}).
            callback: Function to call with ToolResult when done.
                      Called FROM the worker thread — be careful with UI!
        """
        if self._running:
            return  # Don't start twice

        self._running = True

        def worker():
            start_time = time.time()
            try:
                data = self._execute(params)
                duration = time.time() - start_time
                result = ToolResult(
                    tool_name=self.name,
                    success=True,
                    data=data,
                    duration=duration,
                    xp_reward=self.xp_reward(data),
                )
            except Exception as e:
                duration = time.time() - start_time
                result = ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=str(e),
                    duration=duration,
                    xp_reward=0,
                )
            finally:
                self._running = False

            if callback:
                callback(result)

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def _execute(self, params):
        """Override this in subclass: do the actual network operation.

        Args:
            params: Dict of tool-specific parameters.

        Returns:
            Dict of result data.
        """
        raise NotImplementedError("Subclass must implement _execute()")

    def xp_reward(self, result_data):
        """How much XP this operation awards. Override for custom values."""
        return 10  # Default: 10 XP per operation

    def food_value(self, result_data):
        """How much to feed the pet. Override for custom values."""
        return 5  # Default: restores 5 hunger
