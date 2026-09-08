import urllib.request
import json
import os
import sys

def execute_in_gui(python_code_str):
    url = "http://127.0.0.1:30010/remote/object/call"
    
    # 写入一个临时 python 脚本让 UE 执行
    tmp_script = "/Users/cc/Desktop/GGBOM/xxxx/Content/Python/temp_gui_exec.py"
    with open(tmp_script, "w", encoding="utf-8") as f:
        f.write(python_code_str)
        
    cmd = f"py temp_gui_exec.py"
    payload = {
        "objectPath": "/Script/Engine.Default__KismetSystemLibrary",
        "functionName": "ExecuteConsoleCommand",
        "parameters": {
            "Command": cmd
        },
        "generateTransaction": False
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            print("Editor GUI Remote Execution Triggered: OK")
            return True
    except Exception as e:
        print(f"Failed to execute in Editor GUI: {e}")
        return False

if __name__ == "__main__":
    code = """
import unreal
unreal.log("==================================================")
unreal.log("🚀 GUI EDITOR: 官方 API 热重载与资产生效流水线启动...")
unreal.log("==================================================")
"""
    execute_in_gui(code)
