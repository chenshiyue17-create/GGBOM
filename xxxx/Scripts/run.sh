#!/bin/zsh
set -euo pipefail
PROJECT_DIR="${0:A:h:h}"
python3 "$PROJECT_DIR/main.py"
