"""Diagrams for the code guide (run from the project folder)."""
import json
import math
import os
import sys

import cv2
import matplotlib
import numpy as np
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

OUT = sys.argv[1]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 200, "savefig.bbox": "tight"})
INK, MUTED, BLUE, ORANGE, GREEN, RED, PURPLE = "#1f2328", "#6e7781", "#2f6fbd", "#d9822b", "#2e9e4f", "#c9372c", "#8250df"


def save(fig, name):
    fig.savefig(os.path.join(OUT, name))
    plt.close(fig)


def box(ax, x, y, w, h, text, color, sub=None, fs=10):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=color + "22", ec=color, lw=1.6))
    ax.text(x + w / 2, y + h / 2 + (0.12 if sub else 0), text, ha="center", va="center",
            fontsize=fs, fontweight="bold", color=INK)
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.2, sub, ha="center", va="center", fontsize=7.5, color=MUTED)


def arrow(ax, p, q, color=MUTED, text=None, rad=0.0, fs=7.5):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=12, lw=1.3, color=color,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=2, shrinkB=2))
    if text:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.12, text, ha="center", fontsize=fs, color=color)


# ---------------------------------------------------------------- architecture --
fig, ax = plt.subplots(figsize=(10, 6.2))
ax.set_xlim(0, 10); ax.set_ylim(0, 6.4); ax.axis("off")
box(ax, 4.0, 5.5, 2.0, 0.7, "main.py", INK, "command line")
box(ax, 4.0, 4.3, 2.0, 0.75, "App", INK, "app.py: scene switch")
box(ax, 7.0, 4.3, 2.0, 0.75, "Settings", INK, "settings.py -> config")
box(ax, 0.2, 2.9, 1.75, 0.8, "Menu", BLUE, "menu.py + ui.py", fs=9)
box(ax, 2.1, 2.9, 1.75, 0.8, "Game", BLUE, "game.py", fs=9)
box(ax, 4.0, 2.9, 1.75, 0.8, "TestScene", BLUE, "test_scene.py", fs=9)
box(ax, 5.9, 2.9, 1.75, 0.8, "OptionsScene", BLUE, "options_menu.py", fs=9)
box(ax, 7.8, 2.9, 2.0, 0.8, "Display", BLUE, "display.py: window", fs=9)
box(ax, 0.2, 1.4, 2.2, 0.8, "GameMap", GREEN, "maps.py")
box(ax, 0.2, 0.2, 1.05, 0.8, "Terrain", GREEN, "SDF", fs=9)
box(ax, 1.35, 0.2, 1.05, 0.8, "Flag", GREEN, "flag.py", fs=9)
box(ax, 2.7, 1.4, 2.2, 0.8, "Character", ORANGE, "character.py")
box(ax, 2.7, 0.2, 2.2, 0.8, "CharacterSprites", ORANGE, "assets.py")
box(ax, 5.2, 1.4, 1.1, 0.8, "Viewport", ORANGE, "camera", fs=9)
box(ax, 6.5, 1.4, 3.3, 0.8, "InputSource", PURPLE, "inputs.py (interface)")
box(ax, 6.5, 0.2, 1.55, 0.8, "VisionInput", PURPLE, "vision.py", fs=9)
box(ax, 8.25, 0.2, 1.55, 0.8, "KeyboardInput", PURPLE, "inputs.py", fs=9)
arrow(ax, (5, 5.5), (5, 5.05))
for x in (1.075, 2.975, 4.875, 6.775):
    arrow(ax, (5, 4.3), (x, 3.7))
arrow(ax, (6.0, 4.67), (7.0, 4.67), text="loads")
arrow(ax, (6.8, 3.7), (7.6, 4.3), text="changes")
arrow(ax, (6.0, 4.45), (8.8, 3.7))
arrow(ax, (1.075, 2.9), (1.1, 2.2)); arrow(ax, (0.75, 1.4), (0.72, 1.0)); arrow(ax, (1.9, 1.4), (1.87, 1.0))
arrow(ax, (3.2, 2.9), (3.6, 2.2)); arrow(ax, (3.8, 1.4), (3.8, 1.0)); arrow(ax, (3.7, 2.9), (5.6, 2.2))
arrow(ax, (2.5, 2.9), (2.1, 2.2), text="uses map")
arrow(ax, (7.3, 1.4), (7.3, 1.0)); arrow(ax, (9.0, 1.4), (9.0, 1.0))
arrow(ax, (8.8, 2.9), (8.3, 2.2), text="camera picture", rad=0.0)
ax.text(5, 6.32, "Who creates / uses whom", ha="center", fontsize=12, fontweight="bold", color=INK)
for c, t, x in ((BLUE, "screens (scenes)", 0.3), (GREEN, "level data", 2.3), (ORANGE, "character + view", 4.0),
                (PURPLE, "player input", 6.2)):
    ax.add_patch(FancyBboxPatch((x, -0.35), 0.25, 0.2, boxstyle="round,pad=0.01", fc=c + "22", ec=c))
    ax.text(x + 0.35, -0.25, t, va="center", fontsize=8, color=MUTED)
ax.set_ylim(-0.45, 6.5)
save(fig, "fig_architecture.png")

# ------------------------------------------------------------------- threads --
fig, ax = plt.subplots(figsize=(10, 4.6))
ax.set_xlim(0, 10); ax.set_ylim(0, 4.8); ax.axis("off")
ax.add_patch(FancyBboxPatch((0.1, 2.55), 9.8, 2.1, boxstyle="round,pad=0.02", fc=PURPLE + "0d", ec=PURPLE, lw=1, ls="--"))
ax.text(0.25, 4.45, "vision thread  (VisionInput._loop, ~30-40 FPS)", fontsize=9, color=PURPLE, fontweight="bold")
steps = [("webcam\nframe", "cap.read()"), ("mirror", "cv2.flip"), ("YOLO pose", "17 keypoints\nper person"),
         ("players", "biggest n,\nleft to right"), ("faces", "MediaPipe,\nmatch to body"),
         ("PlayerState", "angles, mouth,\nhead tilt"), ("preview", "draw skeleton\n+ lips")]
for i, (t, s) in enumerate(steps):
    x = 0.25 + i * 1.38
    box(ax, x, 2.9, 1.2, 0.95, t, PURPLE, fs=9)
    ax.text(x + 0.6, 2.67, s, ha="center", va="top", fontsize=6.8, color=MUTED)
    if i:
        arrow(ax, (x - 0.18, 3.37), (x, 3.37))
ax.add_patch(FancyBboxPatch((3.3, 1.55), 3.4, 0.62, boxstyle="round,pad=0.02", fc="#fff8c5", ec=ORANGE, lw=1.4))
ax.text(5.0, 1.86, "shared results, guarded by a Lock:  _states, _preview", ha="center", fontsize=8.5, color=INK)
arrow(ax, (7.15, 2.9), (6.3, 2.17), PURPLE); arrow(ax, (8.6, 2.9), (6.7, 2.05), PURPLE)
ax.add_patch(FancyBboxPatch((0.1, 0.05), 9.8, 1.25, boxstyle="round,pad=0.02", fc=BLUE + "0d", ec=BLUE, lw=1, ls="--"))
ax.text(0.25, 1.1, "game thread  (Game.run, 60 FPS)", fontsize=9, color=BLUE, fontweight="bold")
gsteps = ["events", "get_players()", "apply_players", "physics x3", "camera, timer,\nflag", "draw + present"]
for i, t in enumerate(gsteps):
    x = 0.25 + i * 1.62
    box(ax, x, 0.18, 1.42, 0.7, t, BLUE, fs=8.5)
    if i:
        arrow(ax, (x - 0.2, 0.53), (x, 0.53))
arrow(ax, (4.4, 1.55), (2.6, 0.9), ORANGE, "newest states", fs=7)
arrow(ax, (6.3, 1.55), (8.6, 0.9), ORANGE, "newest picture", fs=7)
save(fig, "fig_threads.png")

# ---------------------------------------------------------------------- SDF --
fg = np.array(Image.open("assets/foreground.png"))[:, :, 3] > 127
crop = fg[1050:1900, 1950:3300]
crop = cv2.resize(crop.astype(np.uint8), (crop.shape[1] // 2, crop.shape[0] // 2), interpolation=cv2.INTER_NEAREST) > 0
out = cv2.distanceTransform((~crop).astype(np.uint8), cv2.DIST_L2, 5)
ins = cv2.distanceTransform(crop.astype(np.uint8), cv2.DIST_L2, 5)
sdf = (out - ins) * 2
fig, axs = plt.subplots(1, 2, figsize=(11, 4.1))
axs[0].imshow(crop, cmap="Greys", interpolation="nearest"); axs[0].set_title("solid mask (foreground alpha > 127)", fontsize=10)
lim = 120
im = axs[1].imshow(np.clip(sdf, -lim, lim), cmap="RdBu", vmin=-lim, vmax=lim)
axs[1].contour(sdf, levels=[0], colors=INK, linewidths=1.2)
axs[1].contour(sdf, levels=[-60, -30, 30, 60, 90], colors=MUTED, linewidths=0.5, linestyles="--")
axs[1].set_title("signed distance (px): blue = air, red = inside rock", fontsize=10)
# normal arrows at a few points
ys, xs = np.mgrid[30:crop.shape[0]:70, 30:crop.shape[1]:70]
gy, gx = np.gradient(sdf)
for y, x in zip(ys.ravel(), xs.ravel()):
    if abs(sdf[y, x]) < 70:
        n = np.hypot(gx[y, x], gy[y, x]) + 1e-9
        axs[1].arrow(x, y, gx[y, x] / n * 22, gy[y, x] / n * 22, head_width=6, color=INK, lw=0.8)
for a in axs:
    a.set_xticks([]); a.set_yticks([])
fig.colorbar(im, ax=axs[1], fraction=0.04)
save(fig, "fig_sdf.png")

# ------------------------------------------------------------- leg geometry --
fig, axs = plt.subplots(1, 2, figsize=(11, 4.6))
ax = axs[0]
ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-3.2, 3.6); ax.set_ylim(-3.3, 1.4)
ax.add_patch(Circle((0, 0), 1, fc="#e8b4b0", ec=INK, lw=2))
ax.text(0, 0, "body\n(head)", ha="center", va="center", fontsize=9)
hip = np.array([0.8, -0.6]); th, bend = 50, -40
d1 = np.array([math.sin(math.radians(th)), -math.cos(math.radians(th))])
knee = hip + 1.5 * d1
d2 = np.array([math.sin(math.radians(th + bend)), -math.cos(math.radians(th + bend))])
foot = knee + 1.6 * d2
ax.plot(*zip(hip, knee, foot), color=INK, lw=4, solid_capstyle="round")
ax.add_patch(Circle(foot, 0.28, fc="#e05b4f", ec=INK))
for p, t, o in ((hip, "hip", (0.12, 0.12)), (knee, "knee", (-0.75, 0.05)), (foot, "foot\n(collision circle)", (0.35, -0.1))):
    ax.plot(*p, "o", color=BLUE); ax.text(p[0] + o[0], p[1] + o[1], t, fontsize=9, color=BLUE)
ax.plot([hip[0], hip[0]], [hip[1], hip[1] - 1.6], ls=":", color=MUTED)
ax.plot([knee[0], knee[0] + 1.3 * d1[0]], [knee[1], knee[1] + 1.3 * d1[1]], ls=":", color=MUTED)
ax.annotate("", xy=hip + 0.95 * d1, xytext=(hip[0], hip[1] - 0.95),
            arrowprops=dict(arrowstyle="->", color=ORANGE, connectionstyle="arc3,rad=0.35", lw=1.5))
ax.text(hip[0] - 2.75, hip[1] - 1.45, "thigh = 50\n(from straight down,\n+ = away from body)", fontsize=8, color=ORANGE)
ax.annotate("", xy=knee + 0.85 * d2, xytext=knee + 0.85 * d1,
            arrowprops=dict(arrowstyle="->", color=GREEN, connectionstyle="arc3,rad=0.4", lw=1.5))
ax.text(knee[0] + 0.9, knee[1] - 0.95, "bend = -40\n(shin minus thigh)", fontsize=8, color=GREEN)
ax.set_title("right leg: angles in the 'outward' convention", fontsize=10)
ax = axs[1]
ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-3.3, 3.3); ax.set_ylim(-2.6, 2.6)
ax.add_patch(Circle((0, 0), 0.6, fc="#e8b4b0", ec=INK, lw=1.5))
for side in (-1, 1):
    for a, lab in ((0, "0  down"), (90, "90  out"), (180, "180  up"), (45, "45")):
        dd = np.array([side * math.sin(math.radians(a)), -math.cos(math.radians(a))])
        p0 = dd * 0.65
        p1 = dd * 2.0
        ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="->", color=BLUE if side > 0 else PURPLE, lw=1.3))
        ax.text(*(dd * 2.35), lab, ha="center", va="center", fontsize=8, color=BLUE if side > 0 else PURPLE)
ax.text(-2.4, -2.45, "left legs (side = -1):\nmirrored", fontsize=8.5, color=PURPLE, ha="center")
ax.text(2.4, -2.45, "right legs (side = +1)", fontsize=8.5, color=BLUE, ha="center")
ax.set_title("the same thigh angle points outward on both sides", fontsize=10)
save(fig, "fig_angles.png")

# ---------------------------------------------------------------- keypoints --
fig, axs = plt.subplots(1, 2, figsize=(11, 5.0), gridspec_kw={"width_ratios": [1.1, 1]})
ax = axs[0]
kp = {0: (0, 8.4), 1: (-0.5, 8.95), 2: (0.5, 8.95), 3: (-1.15, 8.6), 4: (1.15, 8.6), 5: (-1.6, 7.2), 6: (1.6, 7.2),
      7: (-2.8, 6.0), 8: (2.9, 8.1), 9: (-3.3, 4.6), 10: (3.2, 9.6), 11: (-1.0, 4.0), 12: (1.0, 4.0),
      13: (-1.2, 2.0), 14: (1.2, 2.0), 15: (-1.3, 0.0), 16: (1.3, 0.0)}
names = ["nose", "L eye", "R eye", "L ear", "R ear", "L shoulder", "R shoulder", "L elbow", "R elbow", "L wrist",
         "R wrist", "L hip", "R hip", "L knee", "R knee", "L ankle", "R ankle"]
edges = [(0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 11), (6, 12), (11, 12), (5, 7), (7, 9), (6, 8), (8, 10),
         (11, 13), (13, 15), (12, 14), (14, 16)]
for i, j in edges:
    arm = {i, j} <= {5, 7, 9} or {i, j} <= {6, 8, 10}
    ax.plot(*zip(kp[i], kp[j]), color=RED if arm else "#9aa0a6", lw=4 if arm else 2.2, solid_capstyle="round")
head_lab = {0: (0, -0.55, "center"), 1: (-0.15, 0.3, "right"), 2: (0.15, 0.3, "left"),
            3: (-0.2, -0.15, "right"), 4: (0.2, -0.15, "left")}
for k, (x, y) in kp.items():
    ax.plot(x, y, "o", color=INK, ms=4)
    if k in head_lab:
        dx, dy, ha = head_lab[k]
        ax.text(x + dx, y + dy, f"{k} {names[k]}", fontsize=7, ha=ha, color=INK)
    else:
        ax.text(x + (0.18 if x >= 0 else -0.18), y + 0.1, f"{k} {names[k]}", fontsize=7,
                ha="left" if x >= 0 else "right", color=INK)
ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-6, 6); ax.set_ylim(-0.6, 10.2)
ax.set_title("COCO 17 keypoints (YOLO pose output);\ncontrolling arms coloured, rest grey", fontsize=10)
ax = axs[1]
ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-2.6, 2.6); ax.set_ylim(-2.2, 2.4)
t = np.linspace(0, 2 * np.pi, 100)
ax.plot(1.8 * np.cos(t), 2.1 * np.sin(t) * 1.0, color="#bbb")
up = np.array([[-1, -0.9], [-0.5, -0.65], [0, -0.7], [0.5, -0.65], [1, -0.9]])
lo = np.array([[-1, -0.9], [-0.5, -1.4], [0, -1.5], [0.5, -1.4], [1, -0.9]])
ax.plot(*up.T, color=RED, lw=2); ax.plot(*lo.T, color=RED, lw=2)
for p, t2 in (((0, -0.7), "13"), ((0, -1.5), "14"), ((-1, -0.9), "61"), ((1, -0.9), "291")):
    ax.plot(*p, "o", color=INK); ax.text(p[0] + 0.08, p[1] + 0.12, t2, fontsize=9, fontweight="bold")
ax.annotate("", xy=(0, -1.5), xytext=(0, -0.7), arrowprops=dict(arrowstyle="<->", color=BLUE, lw=1.5))
ax.annotate("", xy=(1, -1.95), xytext=(-1, -1.95), arrowprops=dict(arrowstyle="<->", color=ORANGE, lw=1.5))
ax.text(0.12, -1.12, "gap", color=BLUE, fontsize=9); ax.text(-0.3, -2.18, "width", color=ORANGE, fontsize=9)
for e in (-0.7, 0.7):
    ax.add_patch(Circle((e, 0.6), 0.28, fc="white", ec="#bbb"))
ax.text(0, 1.6, "mouth ratio = gap / width", ha="center", fontsize=11, fontweight="bold")
ax.set_title("4 of the 478 face-mesh points used for the mouth", fontsize=10)
save(fig, "fig_keypoints.png")

# --------------------------------------------------------------- hysteresis --
rng = np.random.default_rng(3)
tt = np.linspace(0, 6, 180)
raw = 0.08 + 0.42 * ((tt > 1.2) & (tt < 2.7)) + 0.3 * ((tt > 3.6) & (tt < 4.1)) + rng.normal(0, 0.05, tt.size)
raw += 0.22 * ((tt > 4.8) & (tt < 6))
ema = np.zeros_like(raw); state = np.zeros_like(raw); s, o = 0.0, False
for i, r in enumerate(raw):
    s = 0.5 * r + 0.5 * s
    if o and s < 0.25:
        o = False
    elif not o and s > 0.35:
        o = True
    ema[i], state[i] = s, o
fig, ax = plt.subplots(figsize=(10, 3.4))
ax.plot(tt, raw, color="#c8ccd1", lw=1, label="raw mouth ratio (one frame)")
ax.plot(tt, ema, color=BLUE, lw=2, label="smoothed (EMA 0.5)")
ax.axhline(0.35, color=GREEN, ls="--", lw=1); ax.text(6.05, 0.35, "open above 0.35", va="center", fontsize=8, color=GREEN)
ax.axhline(0.25, color=RED, ls="--", lw=1); ax.text(6.05, 0.25, "close below 0.25", va="center", fontsize=8, color=RED)
ax.fill_between(tt, 0, 0.6, where=state > 0, color=GREEN, alpha=0.12, step="mid", label="state = OPEN (sticky)")
ax.set_xlim(0, 6); ax.set_ylim(0, 0.65); ax.set_xlabel("time (s)"); ax.set_ylabel("mouth ratio")
ax.legend(loc="upper left", fontsize=8, frameon=False, ncol=3)
ax.set_title("Hysteresis: the score between the two lines keeps the previous state (no flicker)", fontsize=10)
save(fig, "fig_mouth.png")

# --------------------------------------------------------------------- jump --
rec = json.load(open(os.path.join(OUT, "jump.json")))
fig, axs = plt.subplots(1, 3, figsize=(11, 3.3))
axs[0].plot(rec["t"], rec["thigh"], color=ORANGE, lw=2); axs[0].set_title("thigh angle (deg)", fontsize=10)
axs[1].plot(rec["t"], rec["vy"], color=BLUE, lw=2); axs[1].set_title("upward speed (px/s)", fontsize=10)
axs[2].plot(rec["t"], rec["height"], color=GREEN, lw=2); axs[2].set_title("body height above start (px)", fontsize=10)
for a in axs:
    a.set_xlabel("time (s)"); a.axhline(0, color="#ddd", lw=0.8)
fig.suptitle("Recorded from the real physics: legs straighten (limited to 420 deg/s) -> body is pushed up -> it flies",
             fontsize=10, y=1.03)
save(fig, "fig_jump.png")
print("figures written")
