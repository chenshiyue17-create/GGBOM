#!/bin/bash
# =============================================================================
# launch_lightweight_game.sh
# 360x640 极速轻量独立游戏窗口启动脚本
# 最低渲染画质 + 锁定 30 FPS + 无 SplashScreen，秒级启动且完全不卡顿
# =============================================================================

# 自动探测 UnrealEditor 路径
UE_BIN=""
for candidate in \
  "/Volumes/NINJAV 1/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" \
  "/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" \
  "/Volumes/NINJAV/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" \
  "/Volumes/NINJAV 1/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor" \
  "/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor" \
  "/Volumes/NINJAV/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor"; do
  if [ -x "${candidate}" ] || [ -f "${candidate}" ]; then
    UE_BIN="${candidate}"
    break
  fi
done

if [ -z "${UE_BIN}" ]; then
  echo "❌ 未找到 UnrealEditor 可执行文件，请检查外部移动硬盘连接！"
  exit 1
fi

PROJECT="/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"
MAP="${1:-/Game/GGBOM/Maps/MAP_GGBOM_Main}"

echo "================================================================"
echo "🎮 启动 360x640 轻量独立游戏窗口 (StandAlone Game)..."
echo "🗺️ 目标地图: ${MAP}"
echo "================================================================"

"${UE_BIN}" "${PROJECT}" "${MAP}" -game -windowed -ResX=360 -ResY=640 -ForceRes -NoSplash -ExecCmds="sg.ViewDistanceQuality 0,sg.AntiAliasingQuality 0,sg.ShadowQuality 0,sg.PostProcessQuality 0,sg.EffectsQuality 0,sg.FoliageQuality 0,t.MaxFPS 30"
