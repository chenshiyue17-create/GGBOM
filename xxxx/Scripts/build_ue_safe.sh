#!/bin/bash
# =============================================================================
# build_ue_safe.sh
# UE5 安全编译脚本：编译前自动清理 macOS AppleDouble 资源叉文件
# 防止 UnrealBuildTool 扫描到 ._*.uplugin 导致 JsonReaderException 崩溃
# =============================================================================

set -euo pipefail

UE_ROOT="/Volumes/NINJAV 2/UE_5.8/UE_5.8"
PROJECT="/Users/cc/Desktop/GGBOM/xxxx/xxxx.uproject"

echo "================================================================"
echo "  [1/3] 清理 AppleDouble 资源叉文件 (dot_clean)..."
echo "================================================================"

# dot_clean: 把 extended attributes 合并回文件本体并删除 ._* 文件
# -m = merge mode（合并后删除资源叉，不留垃圾）
dot_clean -m "${UE_ROOT}/Engine/Plugins"
dot_clean -m "${UE_ROOT}/Engine/Platforms"
dot_clean -m "${UE_ROOT}/Engine/Extras"

echo "✅ dot_clean 完成"
echo ""

echo "================================================================"
echo "  [2/3] 验证无残留 ._*.uplugin 文件..."
echo "================================================================"

REMAINING=$(find "${UE_ROOT}/Engine" -name '._*.uplugin*' 2>/dev/null | wc -l | tr -d ' ')
if [ "$REMAINING" -gt 0 ]; then
    echo "⚠️  仍有 ${REMAINING} 个残留，强制移除..."
    find "${UE_ROOT}/Engine" -name '._*.uplugin*' -delete 2>/dev/null || true
    echo "✅ 强制删除完成"
else
    echo "✅ 无残留 AppleDouble uplugin 文件"
fi
echo ""

echo "================================================================"
echo "  [3/3] 开始编译 xxxxEditor..."
echo "================================================================"

"${UE_ROOT}/Engine/Build/BatchFiles/Mac/Build.sh" \
    xxxxEditor Mac Development \
    -Project="${PROJECT}" \
    -WaitMutex

echo ""
echo "================================================================"
echo "  ✅ 编译完成！"
echo "================================================================"
