#!/usr/bin/env bash
set -euo pipefail
echo 'BLOCKED: historical full recovery rewrites unrelated assets. Use python tools/dev.py doctor, test, validate and config-plan from the repository root.' >&2
exit 2
