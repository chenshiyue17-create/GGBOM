#!/bin/zsh
set -euo pipefail
PROJECT_DIR="${0:A:h:h}"
python3 -m unittest discover -s "$PROJECT_DIR/tests" -v
