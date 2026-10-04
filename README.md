# All For One

*From The Group MeEeEe 🐑*

A co-op 2D climbing game controlled with your body. Up to four players share one
four-legged character: a webcam tracks everyone's arms, and each arm drives one of
the character's legs. Open your mouth to make your feet sticky and climb walls.
Get the character's head to the flag in the top-right corner as fast as you can.

Two maps: **Mountain** (climb the rocks to the peak) and **Cave** (crawl through the tunnel,
up the shaft and out onto the grass). Pick one after choosing the number of players.

![character](assets/character-demo.png)

## How it plays

- **Arms → legs.** Your shoulder angle sets a leg's hip angle and your elbow angle sets its knee.
- **Physics.** Gravity, plus contact on the feet and head. Push a planted foot into the ground
  to jump; sweep a planted leg to walk.
- **Mouth open = sticky feet.** Your shoes turn green. A sticky foot that touches rock
  glues to it (purple shoe) and can pull the body, so you can hang and climb.
- **Goal.** Touch the flag with the head. The timer stops and your best time is kept for the session.

| Players | Who controls what |
|---|---|
| 1 | Two long legs. Left arm → left leg, right arm → right leg. Tilt your head right/left to choose which foot your open mouth makes sticky. |
| 2 | P1's arms → top legs, P2's arms → bottom legs |
| 3 | P1's arms → top legs, P2's left arm → bottom-left, P3's right arm → bottom-right |
| 4 | One arm each: P1 top-left, P2 top-right, P3 bottom-left, P4 bottom-right |

Players are numbered left to right as they stand in front of the camera. In the camera
preview only the arms that control a leg are coloured (P1 red, P2 green, P3 blue, P4 yellow).

**1P TEST** in the menu shows the character on a white screen so you can check your arm
control, mouth and head tilt without the level.

## Install (once per computer)

Needs Python 3.10 or newer (3.12 recommended). The setup creates a private environment
(`.venv`) with the tested package versions, installs the CUDA build of PyTorch on computers
with an NVIDIA GPU (the CPU build otherwise) and downloads the two AI models.

**Windows:** double-click `setup.bat`

**Linux** (normal x86-64 PC):

```bash
./setup.sh
```

On NVIDIA computers the setup offers TensorRT (about 2x faster pose detection, takes ~10 minutes
to build; the game works without it). On Linux the script also checks the things Linux may be
missing and tells you the exact fix: the `python3-venv` package, OpenCV's `libgl1`, and webcam
permission (`sudo usermod -aG video $USER`).

## Run

**Windows:** double-click `run.bat` - **Linux:** `./run.sh`

Options go after the command, e.g. `run.bat --keyboard` or `./run.sh --source 1`:

| Option | |
|---|---|
| `--source 1` | another webcam (or a video file) |
| `--keyboard` | no camera, keyboard debug controls (see inputs.py) |
| `--debug` | start with collision circles shown |

| Key | Action |
|---|---|
| F11 | fullscreen on/off |
| F5 | restart the level |
| F1 | show collision circles |
| Esc | back to menu / quit |

## Options

**OPTIONS** on the title screen tunes the game without touching code: camera mirroring and
tracking, mouth thresholds (with the live mouth score shown while you tune), head tilt, leg
speed and smoothing, gravity, grip, sticky strength and fullscreen. Changes apply at once and
are saved in `settings.json` (per computer, not in git). **RESET TO DEFAULTS** undoes everything.
Only safe settings with limited ranges are offered, and a broken `settings.json` is ignored.

## Faster detection (NVIDIA GPU)

The game picks the fastest backend it finds: TensorRT, then the GPU, then the CPU. The camera
preview shows which one is in use next to the FPS. The TensorRT engine only works on the GPU it
was built on, so each computer builds its own. The setup offers it; to do it later, install
`requirements-gpu.txt` and run `export_engine.py` with the environment's Python
(`.venv\Scripts\python` on Windows, `.venv/bin/python` on Linux).

## Code guide

`docs/All_For_One_Code_Guide.pdf` explains the whole code: architecture, physics, vision, every
file block by block, and how the AI models work. To rebuild it after changes:
`pip install -r requirements-dev.txt`, then `python tools/docs/make_docs.py`.

## Code

| File | What it does |
|---|---|
| `main.py` | entry point and command-line options |
| `app.py` | owns the window, switches between menu, game and test |
| `display.py` | single-window layout: game left, camera right, fullscreen |
| `menu.py`, `ui.py` | title screen, player picker, buttons |
| `game.py` | the level: physics loop, HUD, timer, flag/finish |
| `test_scene.py` | 1-player test screen |
| `character.py` | legs, kinematics, contact physics, sticky feet |
| `terrain.py` | map image and collision (signed distance field from `foreground.png`) |
| `maps.py` | the maps: loading/scaling, start point, flag (list in `config.MAPS`) |
| `flag.py` | goal flag |
| `viewport.py` | camera that follows the character |
| `assets.py` | character sprite loading, leg stretching, shoe colour filters |
| `vision.py` | webcam thread: YOLO pose + MediaPipe face, players, mouths, head tilt |
| `player_state.py` | arm/leg angle math shared by camera and keyboard input |
| `preview.py` | draws the camera preview |
| `inputs.py` | input interface + keyboard controls |
| `config.py` | every tunable number |
| `export_engine.py` | builds the TensorRT engine |
| `settings.py` | player settings: what can be tuned, safe ranges, settings.json |
| `options_menu.py` | the Options screen |
| `download_models.py` | downloads the AI models (run by the setup) |
| `setup.bat` / `setup.ps1` / `setup.sh` | one-time setup on Windows / Linux |
| `run.bat` / `run.sh` | start the game with its environment |
| `tools/docs/` | rebuilds the PDF code guide |
| `pose_and_face_test.py` | original pose + face detection experiment |
