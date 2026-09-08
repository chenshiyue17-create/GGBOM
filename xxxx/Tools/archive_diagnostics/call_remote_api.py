import urllib.request
import json
import sys

def execute_remote(cmd):
    url = "http://127.0.0.1:30010/remote/object/call"
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
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            res_str = resp.read().decode("utf-8")
            print("Remote Call OK:", res_str)
            return True
    except Exception as e:
        print("Remote Call Failed:", e)
        return False

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "py print('=== OFFICIAL REMOTE API CONNECTED ===')"
    execute_remote(cmd)
