"""All For One - entry point.

    python main.py                  # webcam 0
    python main.py --source 1       # another webcam
    python main.py --keyboard       # no camera, keyboard debug controls (see inputs.py)
    python main.py --debug          # draw collision circles

Install: pip install pygame ultralytics mediapipe opencv-python
"""
import argparse

import config
from app import App
from inputs import KeyboardInput


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=config.CAMERA_SOURCE, help="webcam index or video path")
    ap.add_argument("--model", default=config.POSE_MODEL)
    ap.add_argument("--keyboard", action="store_true", help="play without a camera")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    if args.keyboard:
        source = KeyboardInput()
    else:
        from vision import VisionInput   # heavy imports only in camera mode
        source = VisionInput(args.source, args.model)
    App(source, debug=args.debug).run()


if __name__ == "__main__":
    main()
