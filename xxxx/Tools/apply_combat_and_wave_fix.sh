#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$DIR")"
PROJECT="$ROOT/xxxx.uproject"
SCRIPT="$ROOT/Content/Python/apply_combat_and_wave_fix.py"

# 动态探测 UnrealEditor 路径
UE_BIN=""
for candidate in \
  "/Volumes/NINJAV 1/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" \
  "/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" \
  "/Volumes/NINJAV/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" \
  "/Volumes/NINJAV 1/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor-Cmd" \
  "/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor-Cmd" \
  "/Volumes/NINJAV/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor-Cmd"; do
  if [ -x "${candidate}" ] || [ -f "${candidate}" ]; then
    UE_BIN="${candidate}"
    break
  fi
done

if [ -z "${UE_BIN}" ]; then
  echo "❌ 未找到 UnrealEditor-Cmd，请检查移动硬盘！"
  exit 1
fi

echo "================================================================"
echo "🚀 执行子弹解耦与怪物动态部署流水线..."
echo "📁 引擎: ${UE_BIN}"
echo "📄 脚本: ${SCRIPT}"
echo "================================================================"

"${UE_BIN}" \
  "${PROJECT}" \
  -run=pythonscript \
  -script="${SCRIPT}" \
  -nullrhi \
  -nosound \
  -unattended \
  -nopause \
  -stdout

echo "================================================================"
echo "✅ 执行完毕！"
echo "================================================================"
