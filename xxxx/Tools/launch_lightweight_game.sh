#!/usr/bin/env bash
set -euo pipefail
GGBOM_REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ "$#" -gt 0 ]; then
  exec python3 "$GGBOM_REPO_DIR/tools/dev.py" run --mode lite --map "$1"
fi
exec python3 "$GGBOM_REPO_DIR/tools/dev.py" run --mode lite
