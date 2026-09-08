#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
ENGINE_CMD="/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd"
PROJECT_FILE="/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"

"$ENGINE_CMD" "$PROJECT_FILE" -run=pythonscript -script="$SCRIPT_PATH" -nullrhi -unattended
