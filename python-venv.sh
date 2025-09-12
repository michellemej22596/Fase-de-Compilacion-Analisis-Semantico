#!/bin/bash
set -e

VENV_PATH="/opt/venv"
python3 -m venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"

echo "Virtual environment created and activated at $VENV_PATH"
