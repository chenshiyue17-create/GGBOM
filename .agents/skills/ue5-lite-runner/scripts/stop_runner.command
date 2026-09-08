#!/bin/bash
set -euo pipefail

find_pid_file() {
  if [ -n "${UE_PROJECT:-}" ] && [ -f "$UE_PROJECT" ]; then
    ROOT="$(cd "$(dirname "$UE_PROJECT")" && pwd)"
  else
    FOUND="$(find "$(pwd)" -maxdepth 2 -name "*.uproject" -type f | head -n1 || true)"
    if [ -z "$FOUND" ]; then
      echo "STOP_STATUS=BLOCKED"
      echo "BLOCKING_ERROR=PROJECT_NOT_FOUND"
      exit 2
    fi
    ROOT="$(cd "$(dirname "$FOUND")" && pwd)"
  fi
  PID_FILE="$ROOT/.ue5-lite-runner.pid"
}

find_pid_file

if [ ! -f "$PID_FILE" ]; then
  echo "STOP_STATUS=NO_ACTIVE_RUNNER"
  exit 0
fi

PID="$(cat "$PID_FILE")"

if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  sleep 1
  if kill -0 "$PID" 2>/dev/null; then
    kill -9 "$PID" || true
  fi
  echo "STOP_STATUS=PASS"
  echo "STOPPED_PID=$PID"
else
  echo "STOP_STATUS=STALE_PID"
fi

rm -f "$PID_FILE"
