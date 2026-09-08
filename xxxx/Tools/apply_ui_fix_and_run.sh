#!/bin/bash
# =============================================================================
# apply_ui_fix_and_run.sh
# 1. 无头模式清理世界空间错位 UI，生成标准 UMG HUD 控件并绑定
# 2. 重新启动 360x640 轻量窗口呈现干净规整的画面
# =============================================================================

set -e

UE_BIN="/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
PROJECT="/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"
MAP="/Game/GGBOM/Maps/MAP_GGBOM_Main"

echo "================================================================"
echo "🧹 [1/2] 正在执行 UI 规范化修复 (清理场景错位 UI / 构建 UMG)..."
echo "================================================================"

"${UE_BIN}" \
  "${PROJECT}" \
  -run=pythonscript \
  -script="/Users/cc/Desktop/GGBOM/xxxx/Content/Python/fix_ui_umg_layout.py" \
  -nullrhi \
  -nosound \
  -unattended \
  -nopause \
  -stdout

echo ""
echo "================================================================"
echo "🎮 [2/2] 重新拉起 360x640 轻量游戏窗口..."
echo "================================================================"

"${UE_BIN}" \
  "${PROJECT}" \
  "${MAP}" \
  -game \
  -windowed \
  -ResX=360 \
  -ResY=640 \
  -NoSplash \
  -ExecCmds="sg.ViewDistanceQuality 0,sg.AntiAliasingQuality 0,sg.ShadowQuality 0,sg.PostProcessQuality 0,sg.EffectsQuality 0,sg.FoliageQuality 0,t.MaxFPS 30"
