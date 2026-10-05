#!/usr/bin/env bash
# All For One - one-time setup for Linux (x86-64 PC). From the project folder:
#     ./setup.sh [--tensorrt | --no-tensorrt]
# Creates .venv (a private Python 3.12 environment for the game), installs the pinned
# packages, picks the CUDA (NVIDIA) or CPU build of PyTorch and downloads the models.
# If Python 3.12 is missing (e.g. Ubuntu with 3.14) it can get it with uv, without sudo.
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

step "1/6 Looking for Python 3.12"
# The game needs exactly Python 3.12: newer versions (e.g. Ubuntu's 3.14) do not have
# packages for mediapipe / PyTorch yet. The system Python is never changed.
is312() { "$1" -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)' 2>/dev/null; }
uv_python() {   # uv downloads its own Python 3.12 into the home folder (no sudo)
    uv python install 3.12 && PY="$(uv python find 3.12)"
}
PY=""
for cand in python3.12 python3 python; do
    if command -v "$cand" >/dev/null 2>&1 && is312 "$cand"; then PY="$(command -v "$cand")"; break; fi
done
if [ -z "$PY" ] && command -v uv >/dev/null 2>&1; then
    echo "Python 3.12 is not installed - getting it with uv"
    uv_python
fi
if [ -z "$PY" ]; then
    echo "Python 3.12 is not installed (this computer has: $(python3 --version 2>&1))."
    echo "It can be installed for this user only with 'uv' (https://docs.astral.sh/uv/),"
    echo "without sudo and without changing the system Python."
    answer=n
    if [ -t 0 ]; then read -r -p "Install uv and Python 3.12 now? [y/N] " answer; fi
    case "$answer" in
        [yY]*)
            if command -v curl >/dev/null 2>&1; then curl -LsSf https://astral.sh/uv/install.sh | sh
            else wget -qO- https://astral.sh/uv/install.sh | sh; fi
            export PATH="$HOME/.local/bin:$PATH"
            uv_python ;;
        *)
            fail "Install Python 3.12 one of these ways, then run ./setup.sh again:
  a) uv (any Linux, no sudo):  curl -LsSf https://astral.sh/uv/install.sh | sh
                               then: ~/.local/bin/uv python install 3.12
  b) Ubuntu (deadsnakes):      sudo add-apt-repository ppa:deadsnakes/ppa
                               sudo apt install python3.12 python3.12-venv" ;;
    esac
fi
[ -n "$PY" ] && is312 "$PY" || fail "Could not get Python 3.12."
"$PY" --version

step "2/6 Creating the environment in .venv"
if [ -x .venv/bin/python ] && ! is312 .venv/bin/python; then
    echo ".venv was made with $(.venv/bin/python --version 2>&1) - rebuilding it with Python 3.12"
    rm -rf .venv
fi
if [ ! -x .venv/bin/python ]; then
    "$PY" -m venv .venv || fail "Could not create .venv. On Ubuntu/Debian: sudo apt install python3.12-venv
then run ./setup.sh again."
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
