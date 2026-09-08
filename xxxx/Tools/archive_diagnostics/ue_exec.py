# -*- coding: utf-8 -*-
"""
UE 远程命令与 Python 脚本自动执行器 (Remote Execution Client)
通过 Python Remote Execution 或 HTTP Remote Control 直连 UE5 编辑器。
"""
import sys
import json
import time
import socket
import urllib.request
import urllib.error
from pathlib import Path

HTTP_URL = "http://127.0.0.1:30010/remote/object/call"
INFO_URL = "http://127.0.0.1:30010/remote/info"

def check_http_server():
    try:
        req = urllib.request.Request(INFO_URL)
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                return True, data
    except Exception as e:
        return False, str(e)
    return False, "Unknown"

def run_python_via_http(python_code: str):
    payload = {
        "objectPath": "/Script/PythonScriptPlugin.Default__PythonScriptLibrary",
        "functionName": "ExecutePythonCommand",
        "parameters": {
            "PythonCommand": python_code
        },
        "generateTransaction": True
    }
    req = urllib.request.Request(
        HTTP_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ue_exec.py <script_path_or_code>")
        sys.exit(1)
        
    arg = sys.argv[1]
    if Path(arg).is_file():
        with open(arg, 'r', encoding='utf-8') as f:
            code = f.read()
    else:
        code = arg

    ok, info = check_http_server()
    if ok:
        print(f"✅ 连接到 UE Remote Control 服务成功: {info}")
        res = run_python_via_http(code)
        print(f"执行结果: {json.dumps(res, ensure_ascii=False, indent=2)}")
    else:
        print(f"⚠️ HTTP 端口未就绪 ({info})，正在检查进程...")

if __name__ == "__main__":
    main()
