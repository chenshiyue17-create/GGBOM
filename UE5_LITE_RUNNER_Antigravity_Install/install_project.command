#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$SCRIPT_DIR/.agents/skills/ue5-lite-runner"

echo "UE5 Lite Runner - Antigravity Installer"
echo "======================================="

if [ -n "${1:-}" ]; then
  PROJECT_ROOT="$1"
else
  read -r -p "请输入 UE5 项目根目录: " PROJECT_ROOT
fi

PROJECT_ROOT="${PROJECT_ROOT/#\~/$HOME}"

if [ ! -d "$PROJECT_ROOT" ]; then
  echo "INSTALL_STATUS=FAIL"
  echo "ERROR=PROJECT_DIRECTORY_NOT_FOUND"
  exit 1
fi

if ! find "$PROJECT_ROOT" -maxdepth 1 -name "*.uproject" -type f | grep -q .; then
  echo "INSTALL_STATUS=FAIL"
  echo "ERROR=UPROJECT_NOT_FOUND_IN_ROOT"
  exit 1
fi

DEST="$PROJECT_ROOT/.agents/skills/ue5-lite-runner"
mkdir -p "$PROJECT_ROOT/.agents/skills"
rm -rf "$DEST"
cp -R "$SRC" "$DEST"

CONFIG="$PROJECT_ROOT/.ue5-lite-runner.json"
if [ ! -f "$CONFIG" ]; then
  cp "$DEST/templates/.ue5-lite-runner.example.json" "$CONFIG"
fi

echo "INSTALL_STATUS=PASS"
echo "INSTALLED_TO=$DEST"
echo "CONFIG=$CONFIG"
echo ""
echo "重启 Antigravity IDE 后使用："
echo "使用 ue5-lite-runner 轻量运行当前项目"
