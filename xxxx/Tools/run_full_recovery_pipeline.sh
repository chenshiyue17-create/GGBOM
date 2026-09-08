#!/bin/bash
set -e

UE_CMD="/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd"
PROJECT="/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"

echo "================================================================"
echo "🔧 第一步：恢复战场视觉实体与双层地图..."
echo "================================================================"
"$UE_CMD" "$PROJECT" -run=PythonScript -script="/Users/cc/Desktop/GGBOM/xxxx/Content/Python/build_master_visual_hud_stage.py" -unattended -nop4 -nosplash

echo "================================================================"
echo "🎥 第二步：统一主正交运行相机 (941x1672)..."
echo "================================================================"
"$UE_CMD" "$PROJECT" -run=PythonScript -script="/Users/cc/Desktop/GGBOM/xxxx/Content/Python/fix_runtime_camera_unify.py" -unattended -nop4 -nosplash

echo "================================================================"
echo "🧍 第三步：恢复角色可见性与 Pawn 相机..."
echo "================================================================"
"$UE_CMD" "$PROJECT" -run=PythonScript -script="/Users/cc/Desktop/GGBOM/xxxx/Content/Python/fix_player_visibility.py" -unattended -nop4 -nosplash

echo "================================================================"
echo "✅ 完整恢复流水线执行完毕！"
echo "================================================================"
