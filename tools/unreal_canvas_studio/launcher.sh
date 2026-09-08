#!/bin/bash
# ==============================================================================
# Unreal Canvas Studio - 工业级高可用启动器 (Mac Launcher & Health Guard)
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=8899
URL="http://localhost:${PORT}"
LOG_FILE="${DIR}/server.log"

# 解析目标子路由（例如 --slicer）
TARGET_PATH=""
if [[ "$*" == *"--slicer"* ]] || [[ "$1" == "slicer" ]]; then
  TARGET_PATH="/slicer"
fi
TARGET_URL="${URL}${TARGET_PATH}"

# 1. 智能探测具备核心依赖 (numpy, PIL, scipy 等) 的 Python 解释器
find_valid_python() {
  local CANDIDATES=(
    "$UCS_PYTHON"
    "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"
    "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3"
    "/opt/homebrew/bin/python3"
    "/usr/local/bin/python3"
    "$(which python3 2>/dev/null)"
  )

  # 尝试从用户交互式 shell (zsh) 导出环境
  if command -v zsh >/dev/null 2>&1; then
    local USER_PY
    USER_PY=$(zsh -ilc 'which python3' 2>/dev/null)
    if [ -n "$USER_PY" ]; then
      CANDIDATES+=("$USER_PY")
    fi
  fi

  # 遍历候选路径，优先选取包含核心依赖的环境
  for py in "${CANDIDATES[@]}"; do
    if [ -n "$py" ] && [ -x "$py" ]; then
      if "$py" -c "import numpy, PIL" >/dev/null 2>&1; then
        echo "$py"
        return 0
      fi
    fi
  done

  # 降级：未通过依赖校验时返回首个存在的 python3
  for py in "${CANDIDATES[@]}"; do
    if [ -n "$py" ] && [ -x "$py" ]; then
      echo "$py"
      return 1
    fi
  done

  echo "/usr/bin/python3"
  return 1
}

PYTHON_BIN=$(find_valid_python)

echo "============================================================"
echo "🚀 启动 Unreal Canvas Studio (通用 UE5 可视化开发套件)"
echo "============================================================"
echo "• 目录: $DIR"
echo "• 端口: $PORT"
echo "• 目标: $TARGET_URL"
echo "• Python 解释器: $PYTHON_BIN"
echo "• 日志: $LOG_FILE"

# 2. 检查 Python 核心依赖完整性
if ! "$PYTHON_BIN" -c "import numpy, PIL" >/dev/null 2>&1; then
  echo "❌ 错误: 当前 Python ($PYTHON_BIN) 缺少核心运行依赖 (numpy / pillow)！"
  osascript -e 'display alert "启动失败：缺少依赖" message "未检测到安装了 numpy/pillow 的 Python 3 环境。\n请在终端执行: pip3 install numpy pillow scipy scikit-image"' 2>/dev/null
  exit 1
fi

# 3. 检查服务是否已在运行
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${URL}/api/project/info" 2>/dev/null)

if [ "$STATUS_CODE" = "200" ]; then
  echo "🟢 服务已在运行中，直接唤起浏览器！"
  osascript -e 'display notification "Unreal Canvas Studio 已就绪，已唤起浏览器！" with title "Unreal Canvas Studio" sound name "Glass"' 2>/dev/null
  open "$TARGET_URL"
  exit 0
fi

# 4. 若未运行，检查端口是否被残留进程占用
OCCUPIED_PID=$(lsof -ti tcp:${PORT} 2>/dev/null)
if [ -n "$OCCUPIED_PID" ]; then
  echo "⚠️ 发现残留旧进程 (PID: $OCCUPIED_PID)，正在优雅重置..."
  kill -9 $OCCUPIED_PID 2>/dev/null
  sleep 1
fi

# 5. 启动后台守护进程
echo "⚡ 正在启动独立通用服务进程..."
nohup "$PYTHON_BIN" "${DIR}/server.py" --project "/Users/cc/Desktop/GGBOM/xxxx" --port ${PORT} > "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# 6. 健康轮询检查 (最多等待 8 秒)
MAX_TRIES=16
COUNT=0
IS_READY=0

while [ $COUNT -lt $MAX_TRIES ]; do
  sleep 0.5
  STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${URL}/api/project/info" 2>/dev/null)
  if [ "$STATUS_CODE" = "200" ]; then
    IS_READY=1
    break
  fi
  COUNT=$((COUNT + 1))
done

if [ $IS_READY -eq 1 ]; then
  echo "🎉 服务成功启动并已通过健康检查！"
  echo "👉 正在自动为您打开浏览器: $TARGET_URL"
  osascript -e 'display notification "Unreal Canvas Studio 服务启动成功！" with title "Unreal Canvas Studio" sound name "Glass"' 2>/dev/null
  open "$TARGET_URL"
else
  echo "❌ 服务在 8 秒内未能响应，请检查日志: $LOG_FILE"
  tail -n 20 "$LOG_FILE"
  ERR_MSG=$(tail -n 5 "$LOG_FILE" 2>/dev/null | tr '\n' ' ' | sed 's/"/\\"/g')
  osascript -e "display alert \"启动超时\" message \"Unreal Canvas Studio 服务启动未能及时就绪。\n${ERR_MSG}\"" 2>/dev/null
  exit 1
fi
