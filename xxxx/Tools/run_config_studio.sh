#!/bin/bash
# ==============================================================================
# 《GGBOM: 终末医疗兵》动态配置中心一键启动器
# ==============================================================================

PORT=8899
SERVER_SCRIPT="/Users/cc/Desktop/GGBOM/xxxx/Content/Python/tools/config_studio/server.py"
LOG_FILE="/Users/cc/Desktop/GGBOM/xxxx/output/config_studio.log"

echo "🔍 检查端口 ${PORT} 占用情况..."
PID=$(lsof -ti tcp:${PORT} || true)
if [ -n "${PID}" ]; then
  echo "⚠️ 端口 ${PORT} 已被进程 ${PID} 占用，正在释放..."
  kill -9 ${PID} 2>/dev/null || true
  sleep 1
fi

echo "🚀 正在启动 GGBOM 动态可视化配置工作室..."
python3 "${SERVER_SCRIPT}" > "${LOG_FILE}" 2>&1 &
NEW_PID=$!

sleep 1
if ps -p ${NEW_PID} > /dev/null; then
  echo "✅ 服务已成功启动！PID: ${NEW_PID}"
  echo "🌐 访问地址: http://localhost:${PORT}"
  echo "📄 运行日志: ${LOG_FILE}"
  
  # 自动打开默认浏览器
  if command -v open > /dev/null; then
    open "http://localhost:${PORT}"
  fi
else
  echo "❌ 启动失败，请检查日志: ${LOG_FILE}"
  cat "${LOG_FILE}"
  exit 1
fi
