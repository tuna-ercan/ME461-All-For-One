#!/usr/bin/env bash
# All For One - start the game with the project's environment (run ./setup.sh once first).
# Extra options are passed on, e.g.:  ./run.sh --keyboard
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
    echo "The environment is missing - run ./setup.sh first."
    exit 1
fi
exec .venv/bin/python main.py "$@"
