"""Download the two AI models and report what hardware will be used.

Run by the setup scripts (setup.ps1 / setup.sh) at the end; safe to run again.
    python download_models.py
"""
import importlib.util
import os
import shutil
import urllib.request

import config


def main():
    os.chdir(config.ROOT)            # the game loads the models from the project folder

    if os.path.exists(config.FACE_MODEL):
        print("face model: already there")
    else:
        print("face model: downloading face_landmarker.task ...")
        urllib.request.urlretrieve(config.FACE_URL, config.FACE_MODEL)

    from ultralytics import YOLO      # downloads yolo26n-pose.pt on first use
    YOLO(config.POSE_MODEL)
    print(f"pose model: {config.POSE_MODEL} ready")

    import torch
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)} - pose detection runs on the GPU")
        engine = os.path.exists(os.path.splitext(config.POSE_MODEL)[0] + ".engine")
        trt = importlib.util.find_spec("tensorrt") is not None
        if engine and trt:
            print("TensorRT engine found - fastest mode")
        elif engine:
            print("(a TensorRT engine file exists, but TensorRT is not installed here - it is not used)")
    elif shutil.which("nvidia-smi"):
        print("NVIDIA GPU found but PyTorch cannot use it - the game will run on the CPU.\n"
              "  Usually the NVIDIA driver is too old for CUDA 13: update it to version 580 or newer,\n"
              "  then run the setup again.")
    else:
        print("no NVIDIA GPU - pose detection runs on the CPU (works, about 9 detections/s)")


if __name__ == "__main__":
    main()
