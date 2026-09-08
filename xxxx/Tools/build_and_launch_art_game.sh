#!/bin/bash
# =============================================================================
# build_and_launch_art_game.sh
# 1. 无头模式 (NullRHI) 极速装配 1:1 概念图高精美术关卡与 HUD
# 2. 自动启动 360x640 轻量流畅独立游戏窗口进行视觉呈现
# =============================================================================

set -e

UE_BIN="/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
PROJECT="/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"
MAP="/Game/GGBOM/Maps/MAP_GGBOM_Main"

echo "================================================================"
echo "🎨 [1/3] 装配 1:1 高精美术关卡与 HUD..."
echo "================================================================"

"${UE_BIN}" "${PROJECT}" -run=PythonScript -script="/Users/cc/Desktop/GGBOM/xxxx/Content/Python/build_master_visual_hud_stage.py" -nullrhi -nosound -unattended -nopause -stdout

echo "================================================================"
echo "🎥 [2/3] 统一正交运行相机 (941x1672)..."
echo "================================================================"

"${UE_BIN}" "${PROJECT}" -run=PythonScript -script="/Users/cc/Desktop/GGBOM/xxxx/Content/Python/fix_runtime_camera_unify.py" -nullrhi -nosound -unattended -nopause -stdout

echo "================================================================"
echo "🧍 [3/3] 修复角色可见性与 Pawn 相机..."
echo "================================================================"

"${UE_BIN}" "${PROJECT}" -run=PythonScript -script="/Users/cc/Desktop/GGBOM/xxxx/Content/Python/fix_player_visibility.py" -nullrhi -nosound -unattended -nopause -stdout

echo ""
echo "================================================================"
echo "🎮 启动 360x640 轻量独立游戏窗口 (StandAlone Game)..."
echo "================================================================"

"${UE_BIN}" "${PROJECT}" "${MAP}" -game -windowed -ResX=360 -ResY=640 -ForceRes -NoSplash -ExecCmds="sg.ViewDistanceQuality 0,sg.AntiAliasingQuality 0,sg.ShadowQuality 0,sg.PostProcessQuality 0,sg.EffectsQuality 0,sg.FoliageQuality 0,t.MaxFPS 30"
