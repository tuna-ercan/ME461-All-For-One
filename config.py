"""All tunable numbers live here so gameplay can be tweaked without touching logic."""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(ROOT, "assets")


def asset(name):
    return os.path.join(ASSET_DIR, name)


# ------------------------------------------------------------------ map / view --
VIEW_FRACTION = 1 / 3        # game view shows 1/3 of the map width and height
WINDOW_SCALE = 1.0           # max scale of the window (it also shrinks to fit the screen)
# one window: game screen left, camera right (see display.py), sizes relative to the game view width
LAYOUT_MARGIN = 0.025
LAYOUT_CAMERA_WIDTH = 0.40
LAYOUT_SCREEN_FILL = 0.92    # window may use at most this fraction of the desktop
LAYOUT_BG = (40, 42, 48)
START_FULLSCREEN = False     # F11 toggles fullscreen at any time
FPS = 60
PHYSICS_SUBSTEPS = 3         # physics steps per rendered frame (stability)
CAMERA_LERP = 6.0            # how fast the game view follows the character (1/s)
SKY_COLOR = (135, 206, 235)

# ------------------------------------------------------------ character size --
# All character pngs share a 500x500 canvas with the same scale.
# character-demo.png canvas height = CHARACTER_FRACTION * map height.
CHARACTER_FRACTION = 1 / 8
SPRITE_CANVAS = 500

# Geometry measured on the 500x500 canvas (px)
HEAD_CENTER = (250, 250)
HEAD_RADIUS = 95             # collision circle of the head
LEG_PIVOT = (249.5, 190.5)   # joint at the top of leg-part.png / leg-part-with-shoe.png
SEGMENT_LENGTH = 117         # pivot -> pivot of leg-part.png
FOOT_OFFSET = (20, 160)      # shoe centre from LEG_PIVOT while the sprite hangs down (toe = +x)
FOOT_RADIUS = 30             # collision circle of the shoe

# name: (hip offset from head centre, side (-1 left / +1 right), rest thigh, rest bend)
# Angles in degrees, "outward" convention: 0 = pointing down, 90 = pointing
# sideways away from the body, 180 = pointing up. bend = shin angle - thigh angle.
LEGS = {
    "upper_left":  ((-75, -55), -1, 145, 20),
    "upper_right": ((75, -55), +1, 145, 20),
    "lower_left":  ((-85, 50), -1, 50, -50),
    "lower_right": ((85, 50), +1, 50, -50),
}
# Who drives which leg, per number of players: (player index, body limb, character leg).
# Limbs are named by screen side of the mirrored camera image (= the player's own side).
# Players are numbered left -> right as they stand in front of the camera.
# The character only gets the legs listed in its scheme.
CONTROL_SCHEMES = {
    1: [(0, "left_arm", "lower_left"), (0, "right_arm", "lower_right")],
    2: [(0, "left_arm", "upper_left"), (0, "right_arm", "upper_right"),
        (1, "left_arm", "lower_left"), (1, "right_arm", "lower_right")],
    3: [(0, "left_arm", "upper_left"), (0, "right_arm", "upper_right"),
        (1, "left_arm", "lower_left"), (2, "right_arm", "lower_right")],
    4: [(0, "left_arm", "upper_left"), (1, "right_arm", "upper_right"),
        (2, "left_arm", "lower_left"), (3, "right_arm", "lower_right")],
}
MAX_PLAYERS = 4
# leg length multiplier per player count (only the black sticks stretch, shoes keep their size)
LEG_STRETCH = {1: 1.5}
SHOE_TOP = 300               # canvas y where the shoe starts on leg-part-with-shoe.png

# ----------------------------------------------------------------------- flag --
# flag.png stands on the highest ground in the right-most FLAG_SEARCH part of the map.
FLAG_SEARCH = 0.1            # fraction of the map width searched for the peak
FLAG_FRACTION = 1 / 9        # flag.png canvas height relative to the map height
FLAG_BASE = (160, 492)       # canvas px of flag.png that sits on the ground (pole foot)

# -------------------------------------------------------------------- physics --
GRAVITY = 2000.0             # px/s^2 (map pixels)
MAX_SPEED = 1500.0           # px/s, clamp on body velocity
AIR_DRAG = 0.3               # 1/s
LEG_MAX_SPEED = 420.0        # deg/s, how fast a leg joint can follow the arm
SOLVER_ITERATIONS = 4
WALKABLE_SLOPE = 55.0        # deg; feet only get friction on surfaces flatter than this
CONTACT_EPS = 2.0            # px; a foot this close to the ground still counts as touching
STICKY_GRAB_DIST = 8.0       # px; a sticky foot grabs ground within this distance
STICKY_BREAK_DIST = 40.0     # px; a sticky foot tears off if pulled this far from its anchor
STICKY_STIFFNESS = 0.6
HEAD_FRICTION = 6.0          # 1/s, damping while the head scrapes the ground

# --------------------------------------------------------------------- vision --
CAMERA_SOURCE = "0"          # webcam index or video path
POSE_MODEL = "yolo26n-pose.pt"
# Use yolo26n-pose.engine (TensorRT, made for THIS GPU) when it exists and a GPU is present.
# Rebuild it after changing GPU/driver/TensorRT:  python export_engine.py
USE_TENSORRT = True
FACE_MODEL = os.path.join(ROOT, "face_landmarker.task")
FACE_URL = ("https://storage.googleapis.com/mediapipe-models/face_landmarker/"
            "face_landmarker/float16/1/face_landmarker.task")
MIRROR_CAMERA = True         # flip the webcam so it behaves like a mirror
KEYPOINT_THR = 0.5

# face <-> pose matching (pixel closeness)
FACE_MATCH_FACTOR = 1.0      # max face-to-head distance = factor * shoulder width
FACE_MATCH_MIN_PX = 40
FACE_CROP_FALLBACK = True    # if the full-frame face search misses a player, retry on a head crop
CROP_SCALE = 2.4
CROP_DOWN = 0.25
MIN_CROP = 24
UPSCALE_TO = 256

# mouth -> sticky feet
MOUTH_OPEN_T, MOUTH_CLOSE_T = 0.35, 0.25   # hysteresis on lip gap / lip width
MOUTH_EMA = 0.5
MOUTH_TIMEOUT = 0.5          # s; forget the mouth state if the face is lost for this long

# 1 player: sideways head tilt (roll) picks which foot the open mouth sticks.
# head tilted to the right (right ear lower) -> right-arm leg, tilted left -> left-arm leg.
HEAD_TILT_PLAYERS = {1}      # player counts that use this
HEAD_TILT_ANGLE = 10.0       # deg the ear line must tilt to switch side (in between: keep last)
HEAD_TILT_INVERT = False     # True: swap (tilt right -> left-arm leg)

# arm angles -> legs
ANGLE_EMA = 0.6              # smoothing of arm angles (1 = no smoothing)

# player colours (BGR for OpenCV): red, green, blue, yellow
PLAYER_COLORS_BGR = [(0, 0, 255), (0, 220, 0), (255, 120, 0), (0, 220, 255)]
PLAYER_COLORS_RGB = [tuple(reversed(c)) for c in PLAYER_COLORS_BGR]
BODY_COLOR_BGR = (150, 150, 150)

# ----------------------------------------------------------------------- menu --
GAME_TITLE = "All For One"
GAME_CREDIT = "From The Group MeEeEe"
GAME_CREDIT_EMOJI = "🐑"   # sheep
