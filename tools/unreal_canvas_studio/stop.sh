#!/bin/bash
PORT=8899
PIDS=$(lsof -ti tcp:${PORT} 2>/dev/null)
if [ -n "$PIDS" ]; then
  echo "🛑 正在停止 Unreal Canvas Studio 服务 (PID: $PIDS)..."
  kill -9 $PIDS 2>/dev/null
  echo "✅ 服务已成功停止。"
  osascript -e 'display notification "Unreal Canvas Studio 服务已停止" with title "Unreal Canvas Studio"' 2>/dev/null
else
  echo "ℹ️ 服务未在运行。"
fi
