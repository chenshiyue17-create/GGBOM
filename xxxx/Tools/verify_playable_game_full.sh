#!/usr/bin/env bash
set -euo pipefail
echo 'BLOCKED: timed desktop screenshots do not verify gameplay. Capture a fresh UE run with input/expected/actual assertions; see Docs/MULTI_DEVICE_DEVELOPMENT.md.' >&2
exit 2
