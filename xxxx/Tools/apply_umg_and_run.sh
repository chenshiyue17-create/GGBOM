#!/bin/bash
# =============================================================================
# apply_umg_and_run.sh (带完整反馈日志与状态审计)
# 1. 无头模式执行 UMG 实装并实时回显 Python 构建日志
# 2. 自动检查错误并输出执行状态报告
# 3. 启动 360x640 轻量窗口并跟踪运行时反馈日志
# =============================================================================

set -euo pipefail

UE_BIN="/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
PROJECT="/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"
MAP="/Game/GGBOM/Maps/MAP_GGBOM_Main"
LOG_DIR="/Users/cc/Desktop/GGBOM/xxxx/Saved/Logs"
BUILD_LOG="${LOG_DIR}/UMG_Build_Feedback.log"
RUN_LOG="${LOG_DIR}/Runner_Runtime_Feedback.log"

mkdir -p "${LOG_DIR}"

echo "================================================================"
echo "🚀 [1/3] 正在执行 1:1 概念图 UMG 实装流水线 (无头模式)..."
echo "📄 日志文件: ${BUILD_LOG}"
echo "================================================================"

# 执行无头模式 Python 实装，同时在屏幕上实时回显并存盘
"${UE_BIN}" \
  "${PROJECT}" \
  -run=pythonscript \
  -script="/Users/cc/Desktop/GGBOM/xxxx/Content/Python/rebuild_direction_state_v2.py" \
  -nullrhi \
  -nosound \
  -unattended \
  -nopause \
  -stdout 2>&1 | tee "${BUILD_LOG}"

echo ""
echo "================================================================"
echo "🔍 [2/3] UMG 实装执行结果状态审计:"
echo "================================================================"

grep "DIRECTION_STATE_STATUS=" "${BUILD_LOG}" || true

ERRORS=$(grep -iE "Error:|Exception:" "${BUILD_LOG}" | grep -v "0 Error(s)" || true)
if [ -n "${ERRORS}" ] || ! grep -q "DIRECTION_STATE_STATUS=PASS" "${BUILD_LOG}"; then
    echo "⚠️  构建过程中检测到以下异常:"
    echo "${ERRORS}"
else
    echo "✅ 三套方向状态蓝图已重建、编译并保存通过 (0 Errors)！"
fi

echo ""
echo "================================================================"
echo "🎮 [3/3] 启动 360x640 轻量独立游戏窗口 (StandAlone Game)..."
echo "📄 运行日志: ${RUN_LOG}"
echo "================================================================"

nohup "${UE_BIN}" \
  "${PROJECT}" \
  "${MAP}" \
  -game \
  -windowed \
  -ResX=360 \
  -ResY=640 \
  -NoSplash \
  -ExecCmds="sg.ViewDistanceQuality 0,sg.AntiAliasingQuality 0,sg.ShadowQuality 0,sg.PostProcessQuality 0,sg.EffectsQuality 0,sg.FoliageQuality 0,t.MaxFPS 30" > "${RUN_LOG}" 2>&1 &

RUN_PID=$!
sleep 2

if kill -0 "${RUN_PID}" 2>/dev/null; then
    echo "✅ 游戏窗口已成功启动！"
    echo "   - 进程 PID: ${RUN_PID}"
    echo "   - 窗口规格: 360x640 (9:16 竖屏正交, 锁定 30 FPS)"
    echo "   - 实时日志已挂接至: ${RUN_LOG}"
else
    echo "❌ 游戏启动失败，最近 30 行日志如下:"
    tail -n 30 "${RUN_LOG}" || true
    exit 1
fi
