#!/usr/bin/env bash
set -euo pipefail
GGBOM_REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "$GGBOM_REPO_DIR/tools/dev.py" test
