"""All For One - entry point.

    python main.py                  # webcam 0
    python main.py --source 1       # another webcam
    python main.py --keyboard       # no camera, keyboard debug controls (see inputs.py)
    python main.py --debug          # draw collision circles

Install: pip install pygame ultralytics mediapipe opencv-python

This file only reads the command line, picks an input source (camera or
keyboard) and hands it to App, which runs everything else.
"""
import argparse
import sys

import config
from app import App
from inputs import KeyboardInput


def main():
    # The packages are pinned for Python 3.12 (newer Pythons lack mediapipe / PyTorch
    # builds). run.bat / run.sh use the .venv made by the setup, which is 3.12.
    if sys.version_info[:2] != (3, 12):
        print(f"Warning: this is Python {sys.version.split()[0]}, the game is made for 3.12.\n"
              "Start it with run.bat / ./run.sh (after setup.bat / ./setup.sh).")

    # Describe the command-line options; argparse also builds `--help` from this.
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=config.CAMERA_SOURCE, help="webcam index or video path")
    ap.add_argument("--model", default=config.POSE_MODEL)
    ap.add_argument("--keyboard", action="store_true", help="play without a camera")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    # Both input sources have the same methods (see inputs.InputSource), so the
    # rest of the game never needs to know which one it got.
    if args.keyboard:
        source = KeyboardInput()
    else:
        # Imported here, not at the top: loading torch/ultralytics/mediapipe takes
        # seconds and is not needed in keyboard mode.
        from vision import VisionInput   # heavy imports only in camera mode
        source = VisionInput(args.source, args.model)
    App(source, debug=args.debug).run()


# Run main() only when this file is started directly (python main.py),
# not when another file imports it.
if __name__ == "__main__":
    main()
