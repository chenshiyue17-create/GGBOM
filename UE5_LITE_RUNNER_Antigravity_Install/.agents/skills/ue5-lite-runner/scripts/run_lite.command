#!/bin/bash
set -euo pipefail

find_project_root() {
  if [ -n "${UE_PROJECT:-}" ]; then
    if [ -f "$UE_PROJECT" ]; then
      PROJECT_FILE="$UE_PROJECT"
      PROJECT_ROOT="$(cd "$(dirname "$PROJECT_FILE")" && pwd)"
      return
    fi
  fi

  if [ -f ".ue5-lite-runner.json" ]; then
    CONFIG_FILE="$(pwd)/.ue5-lite-runner.json"
  else
    CONFIG_FILE=""
  fi

  local found=""
  found="$(find "$(pwd)" -maxdepth 1 -name "*.uproject" -type f | head -n 1 || true)"
  if [ -z "$found" ]; then
    found="$(find "$(pwd)" -maxdepth 2 -name "*.uproject" -type f | head -n 1 || true)"
  fi

  if [ -n "$found" ]; then
    PROJECT_FILE="$found"
    PROJECT_ROOT="$(cd "$(dirname "$PROJECT_FILE")" && pwd)"
    if [ -z "$CONFIG_FILE" ] && [ -f "$PROJECT_ROOT/.ue5-lite-runner.json" ]; then
      CONFIG_FILE="$PROJECT_ROOT/.ue5-lite-runner.json"
    fi
    return
  fi

  echo "LITE_RUN_STATUS=BLOCKED"
  echo "BLOCKING_ERROR=UE_PROJECT_NOT_FOUND"
  echo "Set UE_PROJECT=/absolute/path/Game.uproject or run inside the project root."
  exit 2
}

read_config_value() {
  local key="$1"
  local fallback="${2:-}"
  if [ -n "${CONFIG_FILE:-}" ] && [ -f "$CONFIG_FILE" ]; then
    python3 - "$CONFIG_FILE" "$key" "$fallback" <<'PY'
import json, sys
p,key,fallback=sys.argv[1:]
try:
    d=json.load(open(p,'r',encoding='utf-8'))
    v=d.get(key,fallback)
    if isinstance(v,bool): print("true" if v else "false")
    else: print(v)
except Exception:
    print(fallback)
PY
  else
    echo "$fallback"
  fi
}

find_engine() {
  local configured="${UE_ENGINE_ROOT:-}"
  if [ -z "$configured" ]; then
    configured="$(read_config_value engine_root "")"
  fi

  if [ -n "$configured" ]; then
    ENGINE_ROOT="${configured/#\~/$HOME}"
  else
    ENGINE_ROOT="$(python3 - <<'PY'
import glob, os, re
c=glob.glob('/Users/Shared/Epic Games/UE_5.*')
def key(p):
    m=re.search(r'UE_(\d+)\.(\d+)',p)
    return tuple(map(int,m.groups())) if m else (0,0)
print(sorted(c,key=key)[-1] if c else '')
PY
)"
  fi

  if [ -z "$ENGINE_ROOT" ] || [ ! -d "$ENGINE_ROOT" ]; then
    echo "LITE_RUN_STATUS=BLOCKED"
    echo "BLOCKING_ERROR=UE_ENGINE_ROOT_NOT_FOUND"
    echo "Set UE_ENGINE_ROOT=/Users/Shared/Epic Games/UE_5.x"
    exit 3
  fi

  UE_EDITOR="$ENGINE_ROOT/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
  UE_CMD="$ENGINE_ROOT/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor-Cmd"

  if [ ! -x "$UE_EDITOR" ]; then
    echo "LITE_RUN_STATUS=BLOCKED"
    echo "BLOCKING_ERROR=UNREAL_EDITOR_BINARY_NOT_FOUND"
    echo "EXPECTED=$UE_EDITOR"
    exit 4
  fi
}

resolve_common() {
  find_project_root
  find_engine
  START_MAP="${UE_START_MAP:-$(read_config_value start_map "")}"
  MUTE_AUDIO="$(read_config_value mute_audio "false")"
  mkdir -p "$PROJECT_ROOT/Saved/LiteRunner"
  PID_FILE="$PROJECT_ROOT/.ue5-lite-runner.pid"
  RUN_LOG="$PROJECT_ROOT/Saved/LiteRunner/runner-launch.log"
}

resolve_common

ARGS=(
  "$PROJECT_FILE"
)

if [ -n "$START_MAP" ]; then
  ARGS+=("$START_MAP")
fi

ARGS+=(
  "-game"
  "-windowed"
  "-ResX=360"
  "-ResY=640"
  "-NoSplash"
  "-ExecCmds=sg.ViewDistanceQuality 0,sg.AntiAliasingQuality 0,sg.ShadowQuality 0,sg.PostProcessQuality 0,sg.EffectsQuality 0,sg.FoliageQuality 0,t.MaxFPS 30"
)

if [ "$MUTE_AUDIO" = "true" ]; then
  ARGS+=("-NoSound")
fi

echo "MODE=LITE_GAME"
echo "PROJECT=$PROJECT_FILE"
echo "ENGINE=$ENGINE_ROOT"
echo "MAP=${START_MAP:-<GameDefaultMap>}"
echo "WINDOW=360x640"
echo "FPS_CAP=30"

nohup "$UE_EDITOR" "${ARGS[@]}" >"$RUN_LOG" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

sleep 1

if kill -0 "$PID" 2>/dev/null; then
  echo "LITE_RUN_STATUS=STARTED"
  echo "PID=$PID"
  echo "PID_FILE=$PID_FILE"
  echo "LAUNCH_LOG=$RUN_LOG"
  echo "UE_LOG_DIR=$PROJECT_ROOT/Saved/Logs"
else
  echo "LITE_RUN_STATUS=FAIL"
  echo "BLOCKING_ERROR=PROCESS_EXITED_EARLY"
  tail -n 60 "$RUN_LOG" || true
  exit 5
fi
