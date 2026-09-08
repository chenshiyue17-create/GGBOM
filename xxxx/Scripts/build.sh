#!/bin/zsh
set -euo pipefail
PROJECT_DIR="${0:A:h:h}"
UE_CMD="${UE5_EDITOR_CMD:-/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd}"
"$UE_CMD" "$PROJECT_DIR/xxxx.uproject" -Unattended -NoSplash -NullRHI -NoSound -ExecutePythonScript="$PROJECT_DIR/Content/Python/build_ggbom_game.py" -stdout -FullStdOutLogOutput
