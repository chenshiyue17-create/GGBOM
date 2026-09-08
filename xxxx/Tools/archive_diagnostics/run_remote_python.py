#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Connect to running Unreal Engine instance via RemoteExecution and execute hot reload / python code.
"""
from __future__ import annotations

import time
import sys
from pathlib import Path
from remote_execution import RemoteExecution, RemoteExecutionConfig

def main(cmd_to_run: str = "import hot_reload; hot_reload.hot_reload_all()"):
    print("==================================================")
    print("🚀 [AI -> UE 实时远程执行通道] 正在连接虚幻引擎...")
    
    config = RemoteExecutionConfig()
    config.multicast_bind_address = "0.0.0.0"
    config.multicast_group_endpoint = ("239.0.0.1", 6766)
    
    remote_exec = RemoteExecution(config)
    remote_exec.start()
    
    print("⏳ 正在探测运行中的 Unreal Engine 节点 (127.0.0.1:6766)...")
    node_id = None
    for _ in range(20):
        nodes = remote_exec.remote_nodes
        if nodes:
            node_id = nodes[0]["node_id"]
            print(f"  🎉 成功发现虚幻引擎节点: {node_id}")
            print(f"     机器名: {nodes[0].get('machine')}, 项目: {nodes[0].get('project_name')}")
            break
        time.sleep(0.1)
        
    if not node_id:
        print("⚠️ 单播未发现节点，尝试组播探测...")
        remote_exec.stop()
        config.multicast_group_endpoint = ("239.0.0.1", 6766)
        remote_exec = RemoteExecution(config)
        remote_exec.start()
        for _ in range(20):
            nodes = remote_exec.remote_nodes
            if nodes:
                node_id = nodes[0]["node_id"]
                print(f"  🎉 成功发现虚幻引擎节点: {node_id}")
                break
            time.sleep(0.1)

    if not node_id:
        print("❌ 未能发现虚幻引擎节点，请检查引擎是否开启了 Python Remote Execution")
        remote_exec.stop()
        return False
        
    print(f"🔌 正在建立 TCP 远程控制会话到节点: {node_id}...")
    remote_exec.open_command_connection(node_id)
    time.sleep(0.2)
    
    if not remote_exec.has_command_connection():
        print("❌ TCP 控制连接建立失败")
        remote_exec.stop()
        return False
        
    print("⚡ 正在通过 AI 远程管道在虚幻引擎内部执行命令:")
    print(f"   >>> {cmd_to_run}")
    
    res = remote_exec.run_command(cmd_to_run)
    print("==================================================")
    print(f"🏁 执行结果: Success={res.get('success')}")
    if res.get("output"):
        for item in res.get("output"):
            print(f"[{item.get('type')}] {item.get('output')}")
    if res.get("result"):
        print(f"Result: {res.get('result')}")
    print("==================================================")
    
    remote_exec.stop()
    return res.get("success", False)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "import hot_reload; hot_reload.hot_reload_all()"
    main(cmd)
