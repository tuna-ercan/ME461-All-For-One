"""What the game needs to know about each human player, plus the limb-angle math."""
import math
from dataclasses import dataclass, field

import numpy as np

import config

# COCO keypoints used here
L_SH, R_SH, L_HIP, R_HIP = 5, 6, 11, 12
ARM_CHAINS = [(5, 7, 9), (6, 8, 10)]        # shoulder, elbow, wrist
LEG_CHAINS = [(11, 13, 15), (12, 14, 16)]   # hip, knee, ankle
LIMBS = ("left_arm", "right_arm", "left_leg", "right_leg")


@dataclass
class LimbPose:
    """Leg command from one body limb. Degrees, 'outward' convention (see config.LEGS)."""
    thigh: float   # shoulder/hip angle vs torso: 0 = hanging down, + = away from body
    bend: float    # elbow/knee angle: lower segment direction - upper segment direction


@dataclass
class PlayerState:
    visible: bool = False
    limbs: dict = field(default_factory=dict)   # limb name -> LimbPose
    mouth_open: bool = False
    mouth_score: float = 0.0
    face_found: bool = False
    sticky_side: str | None = None   # "left"/"right": only that side's limb sticks, None = all
    head_tilt: float = 0.0           # deg, sideways head roll; > 0 = tilted to the right (1 player)


def _heading(v):
    """Angle of a screen vector measured from 'down', positive towards +x."""
    return math.degrees(math.atan2(v[0], v[1]))


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def limb_chains(xy):
    """limb name -> keypoint chain, by screen side (left = smaller x)."""
    arms = sorted(ARM_CHAINS, key=lambda c: xy[c[0]][0])
    legs = sorted(LEG_CHAINS, key=lambda c: xy[c[0]][0])
    return dict(zip(LIMBS, arms + legs))


def limb_poses(xy, conf, thr=config.KEYPOINT_THR):
    """limb name -> LimbPose for every limb whose three keypoints are visible."""
    ok = conf > thr
    if not (ok[L_SH] and ok[R_SH]):
        return {}
    # torso axis: shoulders -> hips, or straight down if hips are out of frame
    if ok[L_HIP] and ok[R_HIP]:
        down = (xy[L_HIP] + xy[R_HIP]) / 2 - (xy[L_SH] + xy[R_SH]) / 2
    else:
        down = np.array([0.0, 1.0])
    torso = _heading(down)

    out = {}
    for name, (a, b, c) in limb_chains(xy).items():
        if not (ok[a] and ok[b] and ok[c]):
            continue
        side = -1 if name.startswith("left") else 1
        upper = side * _wrap(_heading(xy[b] - xy[a]) - torso)
        lower = side * _wrap(_heading(xy[c] - xy[b]) - torso)
        out[name] = LimbPose(upper, _wrap(lower - upper))
    return out


@dataclass
class AngleSmoother:
    """EMA on angles (wrap-safe) so jittery keypoints don't shake the legs."""
    alpha: float = config.ANGLE_EMA
    value: LimbPose | None = None

    def update(self, new):
        if new is None:
            return self.value
        if self.value is None:
            self.value = LimbPose(new.thigh, new.bend)
        else:
            self.value = LimbPose(
                _wrap(self.value.thigh + self.alpha * _wrap(new.thigh - self.value.thigh)),
                _wrap(self.value.bend + self.alpha * _wrap(new.bend - self.value.bend)))
        return self.value
