"""Build the TensorRT engine for the pose model (takes a few minutes, needs an NVIDIA GPU).

    python export_engine.py

The .engine only works on the GPU / driver / TensorRT version it was built with,
so run this again on another computer or after updating them.
Needs: pip install tensorrt-cu13   (and the CUDA build of torch)
"""
from ultralytics import YOLO

import config

if __name__ == "__main__":
    # format="engine": TensorRT. quantize=16: half-precision numbers (faster, tiny
    # accuracy loss). imgsz=640: the picture size the network works on. device=0: first GPU.
    path = YOLO(config.POSE_MODEL).export(format="engine", quantize=16, imgsz=640, device=0)
    print("saved", path)
