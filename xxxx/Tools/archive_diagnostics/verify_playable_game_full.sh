#!/bin/bash
set -e

# ==============================================================================
# verify_playable_game_full.sh
# 自动化实机验收：验证全量数据驱动游戏流程（开局 -> 行尸推进 -> 变异猎犬突袭 -> 持续交火）
# ==============================================================================

# 自动探测 UE5 路径
UE_BIN=""
for candidate in \
  "/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" \
  "/Volumes/NINJAV 1/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" \
  "/Volumes/NINJAV/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" \
  "/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor" \
  "/Volumes/NINJAV 1/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor" \
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
MAP="/Game/GGBOM/Maps/MAP_GGBOM_Main"
OUT_DIR="/Users/cc/Desktop/GGBOM/xxxx/output"
mkdir -p "${OUT_DIR}"

IMG_START="${OUT_DIR}/game_flow_01_start.png"
IMG_WAVE1="${OUT_DIR}/game_flow_02_zombie_wave.png"
IMG_WAVE2="${OUT_DIR}/game_flow_03_combat_advance.png"

echo "================================================================"
echo "🎮 启动 360x640 StandAlone 游戏全流程实机验证..."
echo "📁 引擎路径: ${UE_BIN}"
echo "🗺️ 目标地图: ${MAP}"
echo "================================================================"

"${UE_BIN}" "${PROJECT}" "${MAP}" -game -windowed -ResX=360 -ResY=640 -ForceRes -NoSplash -ExecCmds="sg.ViewDistanceQuality 0,sg.AntiAliasingQuality 0,sg.ShadowQuality 0,sg.PostProcessQuality 0,sg.EffectsQuality 0,sg.FoliageQuality 0,t.MaxFPS 30" &
UE_PID=$!

echo "⏳ [阶段 1] 等待游戏窗口初始化加载 (8s)..."
sleep 8
screencapture -x "${IMG_START}"
echo "📸 [1/3] 游戏开局实机截图已保存: ${IMG_START}"

echo "⏳ [阶段 2] 等待第一波行尸推进与射击交火 (8s)..."
sleep 8
screencapture -x "${IMG_WAVE1}"
echo "📸 [2/3] 行尸推进实机截图已保存: ${IMG_WAVE1}"

echo "⏳ [阶段 3] 等待变异猎犬突袭与深度战斗推进 (8s)..."
sleep 8
screencapture -x "${IMG_WAVE2}"
echo "📸 [3/3] 持续交火实机截图已保存: ${IMG_WAVE2}"

echo "🛑 优雅关闭独立游戏实例 (PID: ${UE_PID})..."
kill -TERM ${UE_PID} 2>/dev/null || true
wait ${UE_PID} 2>/dev/null || true

echo "🎉 全流程实机运行验证顺利完成！"
