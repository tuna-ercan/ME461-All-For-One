"""What the game needs to know about each human player, plus the limb-angle math.

The pose model gives 17 "keypoints" per person in COCO order:
    0 nose, 1 left eye, 2 right eye, 3 left ear, 4 right ear,
    5 left shoulder, 6 right shoulder, 7 left elbow, 8 right elbow,
    9 left wrist, 10 right wrist, 11 left hip, 12 right hip,
    13 left knee, 14 right knee, 15 left ankle, 16 right ankle
Here they are turned into two angles per limb, which drive one character leg.
"""
import math
from dataclasses import dataclass, field

import numpy as np

import config

# COCO keypoints used here
L_SH, R_SH, L_HIP, R_HIP = 5, 6, 11, 12
ARM_CHAINS = [(5, 7, 9), (6, 8, 10)]        # shoulder, elbow, wrist
LEG_CHAINS = [(11, 13, 15), (12, 14, 16)]   # hip, knee, ankle
LIMBS = ("left_arm", "right_arm", "left_leg", "right_leg")


# @dataclass writes __init__ and printing for us: LimbPose(30.0, -10.0)
@dataclass
class LimbPose:
    """Leg command from one body limb. Degrees, 'outward' convention (see config.LEGS)."""
    thigh: float   # shoulder/hip angle vs torso: 0 = hanging down, + = away from body
    bend: float    # elbow/knee angle: lower segment direction - upper segment direction


@dataclass
class PlayerState:
    """Everything the game reads about one player, refreshed every camera frame."""
    visible: bool = False
    limbs: dict = field(default_factory=dict)   # limb name -> LimbPose
    mouth_open: bool = False
    mouth_score: float = 0.0
    face_found: bool = False
    sticky_side: str | None = None   # "left"/"right": only that side's limb sticks, None = all
    head_tilt: float = 0.0           # deg, sideways head roll; > 0 = tilted to the right (1 player)


def _heading(v):
    """Angle of a screen vector measured from 'down', positive towards +x."""
    # atan2(x, y) instead of the usual atan2(y, x): measures from straight down
    # (screen y grows downward), so an arm hanging down gives 0 degrees.
    return math.degrees(math.atan2(v[0], v[1]))


def _wrap(a):
    """Bring an angle into -180..180."""
    return (a + 180.0) % 360.0 - 180.0


def limb_chains(xy):
    """limb name -> keypoint chain, by screen side (left = smaller x)."""
    # Sides come from where the joints are on screen, not from the model's
    # "left/right" labels: on a mirrored picture those labels can be swapped.
    arms = sorted(ARM_CHAINS, key=lambda c: xy[c[0]][0])
    legs = sorted(LEG_CHAINS, key=lambda c: xy[c[0]][0])
    return dict(zip(LIMBS, arms + legs))


def limb_poses(xy, conf, thr=None):
    """limb name -> LimbPose for every limb whose three keypoints are visible."""
    if thr is None:                 # read now (not at import) so the Options screen can change it
        thr = config.KEYPOINT_THR
    ok = conf > thr                 # True for every keypoint the model is sure enough about
    if not (ok[L_SH] and ok[R_SH]):
        return {}
    # torso axis: shoulders -> hips, or straight down if hips are out of frame
    if ok[L_HIP] and ok[R_HIP]:
        down = (xy[L_HIP] + xy[R_HIP]) / 2 - (xy[L_SH] + xy[R_SH]) / 2
    else:
        down = np.array([0.0, 1.0])
    torso = _heading(down)          # leaning the whole body should not swing the legs

    out = {}
    for name, (a, b, c) in limb_chains(xy).items():     # a = shoulder, b = elbow, c = wrist
        if not (ok[a] and ok[b] and ok[c]):
            continue
        # side = -1 for left limbs: mirror the angles so "away from the body" is
        # positive on both sides (the same convention as the character's legs)
        side = -1 if name.startswith("left") else 1
        upper = side * _wrap(_heading(xy[b] - xy[a]) - torso)   # upper arm direction vs torso
        lower = side * _wrap(_heading(xy[c] - xy[b]) - torso)   # forearm direction vs torso
        out[name] = LimbPose(upper, _wrap(lower - upper))       # bend = forearm relative to upper arm
    return out


@dataclass
class AngleSmoother:
    """EMA on angles (wrap-safe) so jittery keypoints don't shake the legs."""
    alpha: float | None = None       # None = use config.ANGLE_EMA (read live, the Options screen changes it)
    value: LimbPose | None = None

    def update(self, new):
        """Exponential moving average: move a fraction `alpha` of the way to the new
        measurement. Wrapping the difference keeps 179 -> -179 a 2 degree step,
        not a 358 degree swing. A missing measurement keeps the last value."""
        if new is None:
            return self.value
        a = config.ANGLE_EMA if self.alpha is None else self.alpha
        if self.value is None:
            self.value = LimbPose(new.thigh, new.bend)
        else:
            self.value = LimbPose(
                _wrap(self.value.thigh + a * _wrap(new.thigh - self.value.thigh)),
                _wrap(self.value.bend + a * _wrap(new.bend - self.value.bend)))
        return self.value
