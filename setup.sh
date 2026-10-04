#!/usr/bin/env bash
# All For One - one-time setup for Linux (x86-64 PC). From the project folder:
#     ./setup.sh [--tensorrt | --no-tensorrt]
# Creates .venv (a private Python environment for the game), installs the pinned
# packages, picks the CUDA (NVIDIA) or CPU build of PyTorch and downloads the models.
set -euo pipefail
cd "$(dirname "$0")"

TRT=ask
for arg in "$@"; do
    case "$arg" in
        --tensorrt) TRT=yes ;;
        --no-tensorrt) TRT=no ;;
        *) echo "unknown option: $arg"; exit 1 ;;
    esac
done
TORCH=(torch==2.14.1 torchvision==0.29.1)
step() { printf '\n\033[36m== %s\033[0m\n' "$1"; }
fail() { printf '\033[31m%s\033[0m\n' "$1"; exit 1; }

step "1/6 Looking for Python 3.10 or newer"
PY=""
for cand in python3.12 python3.11 python3.10 python3; do
    if command -v "$cand" >/dev/null 2>&1 &&
       "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        PY="$cand"; break
    fi
done
[ -n "$PY" ] || fail "Python 3.10+ not found. On Ubuntu/Debian: sudo apt install python3 python3-venv"
"$PY" --version

step "2/6 Creating the environment in .venv"
if [ ! -x .venv/bin/python ]; then
    "$PY" -m venv .venv || fail "Could not create .venv. On Ubuntu/Debian: sudo apt install python3-venv
(or the versioned package, e.g. python3.12-venv), then run ./setup.sh again."
else
    echo ".venv already exists - updating it"
fi
VPY=.venv/bin/python
"$VPY" -m pip install --upgrade pip --quiet

step "3/6 Installing PyTorch"
GPU=no
if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then GPU=yes; fi
if [ "$GPU" = yes ]; then
    echo "NVIDIA GPU found - installing the CUDA build (large download, a few minutes)"
    "$VPY" -m pip install "${TORCH[@]}" --index-url https://download.pytorch.org/whl/cu130
else
    echo "No NVIDIA GPU - installing the small CPU build"
    "$VPY" -m pip install "${TORCH[@]}" --index-url https://download.pytorch.org/whl/cpu
fi

step "4/6 Installing the game's packages"
"$VPY" -m pip install -r requirements.txt
if ! "$VPY" -c "import cv2" 2>/dev/null; then
    fail "OpenCV cannot load a system library. On Ubuntu/Debian: sudo apt install libgl1 libglib2.0-0
then run ./setup.sh again."
fi

step "5/6 Optional: TensorRT (about 2x faster pose detection)"
if [ "$GPU" = yes ] && [ "$TRT" = ask ]; then
    if [ -t 0 ]; then
        read -r -p "Install TensorRT and build the engine? Takes ~10 minutes [y/N] " answer
        case "$answer" in [yY]*) TRT=yes ;; *) TRT=no ;; esac
    else
        TRT=no
    fi
fi
if [ "$GPU" = yes ] && [ "$TRT" = yes ]; then
    "$VPY" -m pip install -r requirements-gpu.txt
    "$VPY" export_engine.py
else
    echo "skipped (the game works without it)"
fi

step "6/6 Downloading the AI models"
"$VPY" download_models.py

# webcam check: the camera is a /dev/video* device the user must be allowed to read
if ! ls /dev/video* >/dev/null 2>&1; then
    printf '\033[33mNo webcam found (/dev/video*). Plug one in, or play with: ./run.sh --keyboard\033[0m\n'
elif [ ! -r /dev/video0 ]; then
    printf '\033[33mYou may not have permission to use the webcam. Run:\n'
    printf '  sudo usermod -aG video %s\nthen log out and back in.\033[0m\n' "$USER"
fi

printf '\n\033[32mDone! Start the game with:  ./run.sh\033[0m\n'
