"""
netgotchi.pet.pet
~~~~~~~~~~~~~~~~~
The NetGotchi virtual pet — your network companion!

LEARNING NOTES — this module teaches:
  - Python classes with properties (@property decorator)
  - Dataclass-like patterns (storing structured state)
  - Real-time timers using timestamps
  - JSON serialization for save/load
  - Enum-like constants using strings

PET MECHANICS:
    Your pet has stats that change based on:
    - Network events (scans, pings, discoveries)
    - Time passing (mood/hunger decay in real-time)
    - Your care actions (feeding it scan data, running tools)

    The pet evolves through stages based on XP and care quality.
    Different tool usage patterns lead to different evolution paths.
"""

import time
import json

# ── Evolution stages ────────────────────────────────────────────────────
STAGE_EGG = "egg"
STAGE_HATCHLING = "hatchling"
STAGE_JUVENILE = "juvenile"
STAGE_ADULT = "adult"
STAGE_ELDER = "elder"

STAGES = [STAGE_EGG, STAGE_HATCHLING, STAGE_JUVENILE, STAGE_ADULT, STAGE_ELDER]

# XP thresholds to evolve to each stage
EVOLUTION_XP = {
    STAGE_EGG: 0,
    STAGE_HATCHLING: 50,
    STAGE_JUVENILE: 200,
    STAGE_ADULT: 500,
    STAGE_ELDER: 1000,
}

# Pet name at each stage — your pet earns a new name as it grows!
# LEARNING NOTE — dict as a lookup table:
#     This maps each evolution stage to a name. As the pet evolves,
#     its name upgrades too: Bit → Byte → Packet → Frame → Stream.
#     (1 bit → 8 bits = byte → bytes = packet → framed → streaming)
STAGE_NAMES = {
    STAGE_EGG: "Bit",
    STAGE_HATCHLING: "Byte",
    STAGE_JUVENILE: "Packet",
    STAGE_ADULT: "Frame",
    STAGE_ELDER: "Stream",
}

# ── Mood definitions ────────────────────────────────────────────────────
MOOD_ECSTATIC = "ecstatic"    # 80-100
MOOD_HAPPY = "happy"          # 60-79
MOOD_NEUTRAL = "neutral"      # 40-59
MOOD_SAD = "sad"              # 20-39
MOOD_MISERABLE = "miserable"  # 0-19


def _clamp(value, low=0, high=100):
    """Clamp a value between low and high.

    LEARNING NOTE — min/max clamping:
        max(low, min(value, high)) is a classic one-liner for clamping.
        - min(value, high) ensures value ≤ high
        - max(low, ...) ensures value ≥ low
        This is the same as your clamp_int() function in the SDL2 project!
    """
    return max(low, min(value, high))


class Pet:
    """The NetGotchi virtual pet.

    LEARNING NOTE — __init__ and state:
        __init__ is called when you create a Pet: `pet = Pet("Byte")`
        All the self.xyz assignments define the pet's state.
        Python doesn't have "private" variables, but by convention
        _underscored names mean "don't touch from outside."
    """

    def __init__(self, name="Bit"):
        self.name = name

        # Core stats (0-100 range)
        self.mood = 80
        self.hunger = 80       # 100 = full, decays over time
        self.energy = 100      # 100 = fully rested

        # RPG stats
        self.xp = 0
        self.level = 1
        self.stage = STAGE_EGG

        # Tracking
        self.total_scans = 0
        self.total_pings = 0
        self.total_hosts_found = 0
        self.tool_affinity = {}  # {"ping": 10, "nmap": 5, ...}

        # Timestamps for real-time decay
        self._last_update = time.time()
        self._last_fed = time.time()

    # ── Properties ──────────────────────────────────────────────────────

    @property
    def mood_name(self):
        """Get the mood as a descriptive string.

        LEARNING NOTE — @property:
            The @property decorator lets you access a method like an
            attribute: pet.mood_name instead of pet.mood_name().
            It's Python's way of making "computed attributes."
        """
        if self.mood >= 80:
            return MOOD_ECSTATIC
        elif self.mood >= 60:
            return MOOD_HAPPY
        elif self.mood >= 40:
            return MOOD_NEUTRAL
        elif self.mood >= 20:
            return MOOD_SAD
        else:
            return MOOD_MISERABLE

    @property
    def is_hungry(self):
        return self.hunger < 30

    @property
    def is_tired(self):
        return self.energy < 20

    # ── Update ──────────────────────────────────────────────────────────

    def update(self, dt):
        """Update pet stats based on elapsed real time.

        LEARNING NOTE — real-time decay:
            Instead of decaying every frame (which depends on frame rate),
            we decay based on actual elapsed seconds. This means your pet
            gets hungrier even if the game was closed and reopened.

        Args:
            dt: Seconds since last frame (not used directly; we use
                wall-clock time for real-time decay).
        """
        now = time.time()
        elapsed = now - self._last_update
        self._last_update = now

        # Hunger decays ~1 point per 5 minutes
        hunger_decay = elapsed / 300.0
        self.hunger = _clamp(self.hunger - hunger_decay)

        # Energy decays ~1 point per 10 minutes
        energy_decay = elapsed / 600.0
        self.energy = _clamp(self.energy - energy_decay)

        # Mood is influenced by hunger and energy
        target_mood = (self.hunger * 0.4 + self.energy * 0.3 +
                       min(self.mood, 100) * 0.3)
        # Slowly drift toward target
        mood_drift = (target_mood - self.mood) * 0.01
        self.mood = _clamp(self.mood + mood_drift)

        # Check for evolution
        self._check_evolution()

    # ── Actions ─────────────────────────────────────────────────────────

    def feed(self, food_value=10):
        """Feed the pet (e.g., from scan discovery).

        Args:
            food_value: How much hunger to restore.
        """
        self.hunger = _clamp(self.hunger + food_value)
        self.mood = _clamp(self.mood + food_value * 0.3)

    def earn_xp(self, amount, tool_name=None):
        """Award XP from completing a network task.

        LEARNING NOTE — dict.get() with default:
            self.tool_affinity.get(tool_name, 0) returns the current
            count for that tool, or 0 if the tool hasn't been used yet.
            This avoids KeyError exceptions.

        Args:
            amount: XP to award.
            tool_name: Which tool earned this XP (for evolution paths).
        """
        self.xp += amount
        self.level = 1 + self.xp // 100  # Simple: level up every 100 XP

        if tool_name:
            current = self.tool_affinity.get(tool_name, 0)
            self.tool_affinity[tool_name] = current + 1

        # Earning XP makes pet happy
        self.mood = _clamp(self.mood + amount * 0.2)
        self.energy = _clamp(self.energy - 2)  # Working costs energy

    def rest(self):
        """Put the pet to sleep to restore energy."""
        self.energy = _clamp(self.energy + 30)

    def react_to_ping(self, success, rtt_ms=None):
        """React to a ping result.

        Args:
            success: True if ping got a response.
            rtt_ms: Round-trip time in milliseconds (if success).
        """
        self.total_pings += 1
        if success:
            self.mood = _clamp(self.mood + 2)
            if rtt_ms and rtt_ms < 10:
                self.mood = _clamp(self.mood + 3)  # Fast = extra happy
        else:
            self.mood = _clamp(self.mood - 5)  # Failed ping = sad

    def react_to_scan(self, hosts_found=0):
        """React to an nmap or network scan result."""
        self.total_scans += 1
        self.total_hosts_found += hosts_found
        if hosts_found > 0:
            self.feed(hosts_found * 5)
            self.earn_xp(hosts_found * 10, "nmap")

    # ── Evolution ───────────────────────────────────────────────────────

    def _check_evolution(self):
        """Check if the pet should evolve to the next stage.

        LEARNING NOTE — enumerate():
            enumerate() gives you both the index AND the value when
            iterating. So for ['egg', 'hatchling', 'juvenile']:
                i=0, stage='egg'
                i=1, stage='hatchling'
                i=2, stage='juvenile'
        """
        for i, stage in enumerate(STAGES):
            if self.xp >= EVOLUTION_XP[stage]:
                if STAGES.index(self.stage) < i:
                    self.stage = stage
                    # Name evolves with the pet!
                    self.name = STAGE_NAMES[stage]

    # ── Serialization ───────────────────────────────────────────────────

    def to_dict(self):
        """Convert pet state to a dictionary for JSON saving.

        LEARNING NOTE — serialization:
            JSON can only store basic types (str, int, float, list, dict).
            We convert our Pet object to a dict of these basic types.
            This is called "serialization" — converting objects to a
            storable/transmittable format.
        """
        return {
            "name": self.name,
            "mood": self.mood,
            "hunger": self.hunger,
            "energy": self.energy,
            "xp": self.xp,
            "level": self.level,
            "stage": self.stage,
            "total_scans": self.total_scans,
            "total_pings": self.total_pings,
            "total_hosts_found": self.total_hosts_found,
            "tool_affinity": self.tool_affinity,
            "last_update": self._last_update,
            "last_fed": self._last_fed,
        }

    @classmethod
    def from_dict(cls, data):
        """Create a Pet from a saved dictionary.

        LEARNING NOTE — @classmethod:
            A classmethod receives the class itself as the first argument
            (cls) instead of an instance (self). It's used for alternative
            constructors: Pet.from_dict(data) creates a new Pet from
            saved data instead of using Pet(name).
        """
        pet = cls(data.get("name", "Bit"))
        pet.mood = data.get("mood", 80)
        pet.hunger = data.get("hunger", 80)
        pet.energy = data.get("energy", 100)
        pet.xp = data.get("xp", 0)
        pet.level = data.get("level", 1)
        pet.stage = data.get("stage", STAGE_EGG)
        pet.total_scans = data.get("total_scans", 0)
        pet.total_pings = data.get("total_pings", 0)
        pet.total_hosts_found = data.get("total_hosts_found", 0)
        pet.tool_affinity = data.get("tool_affinity", {})
        pet._last_update = data.get("last_update", time.time())
        pet._last_fed = data.get("last_fed", time.time())
        return pet
