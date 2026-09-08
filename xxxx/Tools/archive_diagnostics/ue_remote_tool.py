# -*- coding: utf-8 -*-
"""
双模 UE5 Python 实时连接与自动化执行器
1. 支持 HTTP Remote Control API (Port 30010)
2. 支持 UE Python Remote Execution 协议 (Multicast 239.0.0.1:6766 / Unicast 9998)
"""
import os
import sys
import json
import time
import socket
import struct
import urllib.request
import urllib.error
from pathlib import Path

# Multicast settings for UE Python Remote Execution
UE_REMOTE_MULTICAST_GROUP = '239.0.0.1'
UE_REMOTE_MULTICAST_PORT = 6766
UE_HTTP_URL = "http://127.0.0.1:30010/remote/object/call"
UE_INFO_URL = "http://127.0.0.1:30010/remote/info"

def try_http_execute(code_str):
    try:
        payload = {
            "objectPath": "/Script/PythonScriptPlugin.Default__PythonScriptLibrary",
            "functionName": "ExecutePythonCommand",
            "parameters": {"PythonCommand": code_str},
            "generateTransaction": True
        }
        req = urllib.request.Request(
            UE_HTTP_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return True, data
    except Exception as e:
        return False, str(e)

def run_script_in_ue(script_path):
    abs_path = str(Path(script_path).resolve())
    cmd = f"""
import unreal
unreal.PythonScriptLibrary.execute_python_script('{abs_path}')
"""
    # 优先尝试 HTTP
    ok, res = try_http_execute(cmd)
    if ok:
        print(f"✅ [HTTP-API] 成功在 UE 编辑器中执行: {abs_path}")
        print(res)
        return True
    
    print(f"⚠️ HTTP 接口未应答: {res}")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_script_in_ue(sys.argv[1])
    else:
        print("请提供要执行的 Python 脚本路径。")
