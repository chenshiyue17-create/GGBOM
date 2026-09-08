#!/bin/bash
set -e

UE_BIN="/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
PROJECT="/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"
MAP="/Game/GGBOM/Maps/MAP_GGBOM_Main"
OUT_IMG="/Users/cc/Desktop/GGBOM/xxxx/output/combat_depth_full_runtime.png"

echo "🎮 启动 Standalone 验证全量战斗深化系统（打击感/飘字/主HUD/Boss狂暴）实机..."
"${UE_BIN}" "${PROJECT}" "${MAP}" -game -windowed -ResX=360 -ResY=640 -ForceRes -NoSplash -ExecCmds="sg.ViewDistanceQuality 0,sg.AntiAliasingQuality 0,sg.ShadowQuality 0,sg.PostProcessQuality 0,sg.EffectsQuality 0,sg.FoliageQuality 0,t.MaxFPS 30" &
UE_PID=$!

echo "⏳ 等待游戏窗口初始化渲染 (8s)..."
sleep 8

# 捕获屏幕截图
screencapture -x "${OUT_IMG}"
echo "📸 截图已保存至: ${OUT_IMG}"

# 优雅关闭游戏
kill -TERM ${UE_PID} 2>/dev/null || true
wait ${UE_PID} 2>/dev/null || true
echo "✅ 全量战斗深化验证流程完毕！"
