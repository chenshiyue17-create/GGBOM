#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_SRC="$SCRIPT_DIR/.agents/skills/ue5-blueprint-auditor"

echo ""
echo "UE5 Blueprint Auditor - Antigravity Project Installer"
echo "===================================================="
echo ""

if [ -z "$1" ]; then
  echo "用法:"
  echo "  ./install_project.command /你的/UE5项目根目录"
  echo ""
  echo "例如:"
  echo "  ./install_project.command /Users/cc/Desktop/GGBOM/xxxx"
  echo ""
  read -r -p "请输入 UE5 项目根目录: " PROJECT_ROOT
else
  PROJECT_ROOT="$1"
fi

PROJECT_ROOT="${PROJECT_ROOT/#\~/$HOME}"

if [ ! -d "$PROJECT_ROOT" ]; then
  echo "ERROR: 项目目录不存在: $PROJECT_ROOT"
  exit 1
fi

DEST="$PROJECT_ROOT/.agents/skills/ue5-blueprint-auditor"

mkdir -p "$PROJECT_ROOT/.agents/skills"
rm -rf "$DEST"
cp -R "$SKILL_SRC" "$DEST"

if [ ! -f "$DEST/SKILL.md" ]; then
  echo "ERROR: 安装失败，未找到 $DEST/SKILL.md"
  exit 1
fi

echo ""
echo "INSTALL_STATUS=PASS"
echo "SCOPE=PROJECT"
echo "INSTALLED_TO=$DEST"
echo ""
echo "下一步:"
echo "1. 完全关闭并重新打开 Antigravity IDE 工作区"
echo "2. 在 Agent 中输入:"
echo "   使用 ue5-blueprint-auditor 审核当前 Blueprint 改动；只审计不要修改。"
echo ""
