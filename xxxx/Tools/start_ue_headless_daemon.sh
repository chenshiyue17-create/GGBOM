#!/bin/bash
# =============================================================================
# start_ue_headless_daemon.sh
# 启动常驻 UE5.8 无头模式服务 (Headless Daemon)
# 开启 Remote Control HTTP (30010) 与 Python 远程通信，0 GPU 渲染，不卡顿
# =============================================================================

UE_BIN="/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
PROJECT="/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"

echo "================================================================"
echo "🚀 正在启动 UE5.8 常驻 Headless (NullRHI) 引擎服务..."
echo "================================================================"

"${UE_BIN}" \
  "${PROJECT}" \
  -nullrhi \
  -nosound \
  -unattended \
  -nopause \
  -stdout
