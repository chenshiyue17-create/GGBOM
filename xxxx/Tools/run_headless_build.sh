#!/bin/bash
# =============================================================================
# run_headless_build.sh
# UE5 无头模式 (Headless Commandlet) 资产静默高速写入脚本
# -nullrhi: 禁用图形渲染，0 GPU 开销，不卡顿
# -nosound: 禁用音频
# -unattended: 全自动免交互
# =============================================================================

set -e

UE_BIN="/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
PROJECT="/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"
SCRIPT="${1:-/Users/cc/Desktop/GGBOM/xxxx/Content/Python/master_build_pipeline.py}"

echo "================================================================"
echo "🚀 启动 UE5.8 无头模式 (NullRHI) 执行资产写入流水线..."
echo "📄 目标脚本: ${SCRIPT}"
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
echo "✅ 无头模式构建执行完毕，全量 .uasset 资产已持久化写入磁盘！"
echo "================================================================"
