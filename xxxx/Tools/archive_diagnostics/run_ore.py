
import sys
import time
import os

# 将 Tools 目录加入 sys.path
tools_dir = os.path.dirname(os.path.abspath(__file__))
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

import official_remote_execution as ore

print("[REMOTE_EXEC] 正在启动官方远程执行会话 (多播 239.0.0.1:6766, 绑定 127.0.0.1)...")
remote = ore.RemoteExecution()
remote.start()

# 等待发现节点
found_node = None
for i in range(15):
    nodes = remote.remote_nodes
    if nodes:
        found_node = nodes[0]
        print(f"[REMOTE_EXEC] 🎉 成功发现 UE5 节点: {found_node}")
        break
    time.sleep(0.2)

if not found_node:
    print("[REMOTE_EXEC] ⚠️ 3 秒内未发现 UE5 节点，尝试手动遍历已记录节点...")
else:
    node_id = found_node["node_id"]
    print(f"[REMOTE_EXEC] 🔗 正在建立连接至节点: {node_id}...")
    remote.open_command_connection(node_id)
    print("[REMOTE_EXEC] ⚡ 正在发送全量热更新指令到运行中的虚幻编辑器...")
    res = remote.run_command("import hot_reload; hot_reload.hot_reload_all()", exec_mode=ore.MODE_EXEC_STATEMENT)
    print(f"[REMOTE_EXEC] ✅ 执行结果回传: {res}")
    remote.close_command_connection()

remote.stop()
print("[REMOTE_EXEC] 🏁 会话完成！")
