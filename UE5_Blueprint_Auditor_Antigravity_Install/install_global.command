#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_SRC="$SCRIPT_DIR/.agents/skills/ue5-blueprint-auditor"

echo ""
echo "UE5 Blueprint Auditor - Antigravity Global Installer"
echo "====================================================="
echo ""

# Current Antigravity docs use ~/.gemini/antigravity/skills.
# Some Antigravity distributions/codelabs use ~/.gemini/config/skills.
PRIMARY="$HOME/.gemini/antigravity/skills"
FALLBACK="$HOME/.gemini/config/skills"

DEST_ROOT="$PRIMARY"
mkdir -p "$DEST_ROOT"

DEST="$DEST_ROOT/ue5-blueprint-auditor"
rm -rf "$DEST"
cp -R "$SKILL_SRC" "$DEST"

if [ ! -f "$DEST/SKILL.md" ]; then
  echo "ERROR: 主路径安装失败，尝试兼容路径"
  DEST_ROOT="$FALLBACK"
  mkdir -p "$DEST_ROOT"
  DEST="$DEST_ROOT/ue5-blueprint-auditor"
  rm -rf "$DEST"
  cp -R "$SKILL_SRC" "$DEST"
fi

if [ ! -f "$DEST/SKILL.md" ]; then
  echo "INSTALL_STATUS=FAIL"
  exit 1
fi

echo ""
echo "INSTALL_STATUS=PASS"
echo "SCOPE=GLOBAL"
echo "INSTALLED_TO=$DEST"
echo ""
echo "下一步:"
echo "1. 完全退出并重新打开 Antigravity IDE"
echo "2. 任意项目中输入:"
echo "   使用 ue5-blueprint-auditor 审核当前 Blueprint 改动；只审计不要修改。"
echo ""
