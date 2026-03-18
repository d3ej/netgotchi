"""
netgotchi.save.state
~~~~~~~~~~~~~~~~~~~~
Save and load game state to/from JSON files.

LEARNING NOTES — this module teaches:
  - File I/O in Python (open, read, write)
  - JSON serialization (converting dicts ↔ strings ↔ files)
  - pathlib.Path for cross-platform file paths
  - Error handling for file operations (missing files, corrupt data)
  - The os.makedirs pattern for ensuring directories exist

SAVE FILE LOCATION:
    We store saves in a "saves" folder next to the project root.
    The save file is plain JSON so you can open it in any text editor
    to see (or hack!) your pet's stats.
"""

import json
import os
from pathlib import Path

# Default save directory — next to the project root
# LEARNING NOTE — __file__:
#   __file__ is a special variable that holds the path of the current
#   Python file. We navigate UP from this file's directory to find the
#   project root, then put saves there.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SAVE_DIR = _PROJECT_ROOT / "saves"
DEFAULT_SAVE_FILE = "netgotchi_save.json"


def save_game(pet, filepath=None):
    """Save pet state to a JSON file.

    LEARNING NOTE — json.dump():
        json.dump(data, file_object) writes Python dicts/lists to a file
        as JSON text. The `indent=2` argument makes it human-readable
        (pretty-printed). Without it, everything goes on one line.

    Args:
        pet: A Pet object (must have .to_dict() method).
        filepath: Optional custom path. Defaults to saves/netgotchi_save.json.

    Returns:
        Path where the file was saved.
    """
    if filepath is None:
        filepath = DEFAULT_SAVE_DIR / DEFAULT_SAVE_FILE

    filepath = Path(filepath)

    # LEARNING NOTE — os.makedirs(exist_ok=True):
    #   Creates the directory AND any missing parents. exist_ok=True means
    #   "don't error if it already exists." Without this, saving would fail
    #   the first time because the "saves" folder doesn't exist yet.
    os.makedirs(filepath.parent, exist_ok=True)

    save_data = {
        "version": 1,  # For future save format migration
        "pet": pet.to_dict(),
    }

    with open(filepath, "w") as f:
        json.dump(save_data, f, indent=2)

    return filepath


def load_game(filepath=None):
    """Load pet state from a JSON file.

    LEARNING NOTE — json.load():
        json.load(file_object) reads JSON text from a file and converts
        it back to Python dicts/lists. This is "deserialization" — the
        reverse of json.dump().

    Args:
        filepath: Optional custom path. Defaults to saves/netgotchi_save.json.

    Returns:
        Dict with "pet" key containing pet data, or None if no save exists.
    """
    if filepath is None:
        filepath = DEFAULT_SAVE_DIR / DEFAULT_SAVE_FILE

    filepath = Path(filepath)

    if not filepath.exists():
        return None

    with open(filepath, "r") as f:
        save_data = json.load(f)

    return save_data


def delete_save(filepath=None):
    """Delete a save file (for "New Game" functionality).

    Args:
        filepath: Optional custom path.
    """
    if filepath is None:
        filepath = DEFAULT_SAVE_DIR / DEFAULT_SAVE_FILE

    filepath = Path(filepath)
    if filepath.exists():
        os.remove(filepath)


def has_save(filepath=None):
    """Check if a save file exists.

    Args:
        filepath: Optional custom path.

    Returns:
        True if a save file exists at the path.
    """
    if filepath is None:
        filepath = DEFAULT_SAVE_DIR / DEFAULT_SAVE_FILE
    return Path(filepath).exists()
