"""Player-tunable settings: what can be changed in the Options screen, the safe range
of each value, and saving/loading them to settings.json.

How it works: the game reads all its numbers from `config`. A Setting names one of
those config values; Settings.set() writes the new value straight into `config`
(e.g. config.GRAVITY = 2400), so every part of the game sees it immediately.
settings.json only stores the values the player changed; at start-up they are
put back into `config` before anything else is built.

Only values that cannot break the game are offered, each limited to a safe
range. A missing, broken or hand-edited settings.json never crashes the game:
unknown names and wrong types are ignored and numbers are clamped into range.
"""
import json
import os
from dataclasses import dataclass

import config

SETTINGS_FILE = os.path.join(config.ROOT, "settings.json")
MOUTH_GAP = 0.05     # "close" threshold is kept at least this far below "open"


@dataclass
class Setting:
    key: str             # name of the value in config.py
    label: str           # text shown in the Options screen
    group: str           # tab it appears in
    kind: str            # "float", "int" or "bool"
    lo: float = 0.0      # smallest allowed value (numbers only)
    hi: float = 1.0      # largest allowed value
    step: float = 0.01   # slider step
    unit: str = ""       # shown after the value, e.g. "deg"
    help: str = ""       # one-line explanation shown at the bottom of the screen

    def clamp(self, value):
        """Convert to the right type and force into the safe range (None if impossible)."""
        if self.kind == "bool":
            return value if isinstance(value, bool) else None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        value = min(max(float(value), self.lo), self.hi)
        value = round(round(value / self.step) * self.step, 6)       # snap to the slider step
        return int(round(value)) if self.kind == "int" else float(value)


GROUPS = ["Camera", "Mouth", "Head tilt", "Controls", "Physics", "Display"]

SETTINGS = [
    Setting("MIRROR_CAMERA", "Mirror camera", "Camera", "bool",
            help="Flip the camera picture like a mirror (your right hand shows on the right)."),
    Setting("KEYPOINT_THR", "Joint confidence needed", "Camera", "float", 0.3, 0.8, 0.05,
            help="Lower: arms are tracked in worse light but jitter more. "
                 "Higher: steadier, lost more often."),

    Setting("MOUTH_OPEN_T", "Open above", "Mouth", "float", 0.15, 0.6, 0.01,
            help="Mouth ratio (lip gap / mouth width) needed to turn sticky on. Lower = easier."),
    Setting("MOUTH_CLOSE_T", "Close below", "Mouth", "float", 0.05, 0.55, 0.01,
            help="Ratio below which sticky turns off again. Always kept a bit below 'Open above'."),
    Setting("MOUTH_EMA", "Mouth smoothing", "Mouth", "float", 0.2, 1.0, 0.05,
            help="1 = react instantly, lower = smoother but slower to open/close."),
    Setting("MOUTH_TIMEOUT", "Keep state when face lost", "Mouth", "float", 0.0, 2.0, 0.1, "s",
            help="How long the mouth state is kept when the face is not found for a moment."),

    Setting("HEAD_TILT_ANGLE", "Switch angle", "Head tilt", "float", 5, 25, 1, "deg",
            help="1 player: how far you tilt your head sideways to choose the sticky foot."),
    Setting("HEAD_TILT_INVERT", "Swap sides", "Head tilt", "bool",
            help="1 player: tilt right picks the LEFT foot instead of the right one."),

    Setting("LEG_MAX_SPEED", "Leg speed", "Controls", "float", 240, 720, 10, "deg/s",
            help="How fast the legs follow your arms. Higher = snappier, stronger kicks and jumps."),
    Setting("ANGLE_EMA", "Arm smoothing", "Controls", "float", 0.2, 1.0, 0.05,
            help="1 = legs copy every arm movement, lower = smoother legs but a little delay."),

    Setting("GRAVITY", "Gravity", "Physics", "float", 1200, 3000, 50, "px/s2",
            help="Higher = heavier character: falls faster, jumps lower."),
    Setting("WALKABLE_SLOPE", "Grip on slopes up to", "Physics", "float", 30, 70, 1, "deg",
            help="Feet grip (don't slide) on ground flatter than this, without being sticky."),
    Setting("STICKY_BREAK_DIST", "Sticky foot tears off at", "Physics", "float", 20, 80, 2, "px",
            help="How far a glued foot can be pulled from its spot before it lets go."),

    Setting("START_FULLSCREEN", "Fullscreen", "Display", "bool",
            help="Play in fullscreen (also F11 at any time). Remembered for the next start."),
]
BY_KEY = {s.key: s for s in SETTINGS}


class Settings:
    def __init__(self, path=SETTINGS_FILE):
        self.path = path
        # the values written in config.py = the defaults "Reset to defaults" goes back to
        self.defaults = {s.key: getattr(config, s.key) for s in SETTINGS}

    def get(self, key):
        return getattr(config, key)

    def set(self, key, value):
        """Change one setting (clamped to its safe range) and apply it immediately."""
        setting = BY_KEY.get(key)
        value = setting.clamp(value) if setting else None
        if value is None:
            return
        setattr(config, key, value)
        # keep the mouth thresholds in a valid order (close < open)
        if key == "MOUTH_OPEN_T" and config.MOUTH_CLOSE_T > value - MOUTH_GAP:
            config.MOUTH_CLOSE_T = BY_KEY["MOUTH_CLOSE_T"].clamp(value - MOUTH_GAP)
        if key == "MOUTH_CLOSE_T" and config.MOUTH_OPEN_T < value + MOUTH_GAP:
            config.MOUTH_OPEN_T = BY_KEY["MOUTH_OPEN_T"].clamp(value + MOUTH_GAP)
            config.MOUTH_CLOSE_T = min(config.MOUTH_CLOSE_T, config.MOUTH_OPEN_T - MOUTH_GAP)

    def reset(self):
        """Back to the values written in config.py."""
        for key, value in self.defaults.items():
            setattr(config, key, value)

    def changed(self):
        """Only the settings that differ from the defaults (what gets saved)."""
        return {k: self.get(k) for k in self.defaults if self.get(k) != self.defaults[k]}

    # ------------------------------------------------------------ file --
    def load(self):
        """Apply settings.json if it exists. Anything wrong in it is skipped."""
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return
        except (OSError, ValueError) as e:
            print(f"settings.json ignored ({e}); using defaults")
            return
        if not isinstance(data, dict):
            return
        # open threshold first, so the close threshold is checked against it
        for key in sorted(data, key=lambda k: k != "MOUTH_OPEN_T"):
            if key in BY_KEY:
                self.set(key, data[key])

    def save(self):
        """Write the changed settings; with nothing changed the file is removed."""
        changed = self.changed()
        try:
            if changed:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(changed, f, indent=2)
            elif os.path.exists(self.path):
                os.remove(self.path)
        except OSError as e:
            print(f"could not save settings ({e})")
