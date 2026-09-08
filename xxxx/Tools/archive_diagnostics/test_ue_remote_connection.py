# -*- coding: utf-8 -*-
"""
================================================================================
test_ue_remote_connection.py
探测与连接 UE5 正在运行的实时通信接口:
1. Python Remote Execution (UDP 6766 / TCP)
2. Remote Control HTTP (30010)
================================================================================
"""
import socket
import json
import time
import urllib.request

def test_remote_control_http():
    print("[1] 测试 Remote Control HTTP (http://127.0.0.1:30010/remote/info)...")
    try:
        req = urllib.request.Request("http://127.0.0.1:30010/remote/info")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print("  ✅ Remote Control HTTP 在线！支持路由数:", len(data.get("HttpRoutes", [])))
            return True
    except Exception as e:
        print(f"  ❌ Remote Control HTTP 连接失败: {e}")
        return False

def test_python_remote_execution():
    print("[2] 测试 UE5 Python Remote Execution (UDP 6766 组播/单播发现)...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    msg = json.dumps({
        "version": 1,
        "magic": "ue_py",
        "type": "open_connection",
        "source": "antigravity"
    }).encode("utf-8")
    
    # 尝试发送到单播和组播
    for target in [("127.0.0.1", 6766), ("239.0.0.1", 6766)]:
        try:
            sock.sendto(msg, target)
            print(f"  📡 已向 {target} 发送握手请求...")
        except Exception as e:
            print(f"  ⚠️ 发送到 {target} 失败: {e}")
            
    try:
        data, addr = sock.recvfrom(4096)
        resp = json.loads(data.decode("utf-8"))
        print(f"  🎉 收到 UE5 Python Remote Execution 响应来自 {addr}:")
        print("  ", resp)
        sock.close()
        return resp
    except socket.timeout:
        print("  ⏳ UDP 6766 超时未收到响应 (可能未在 Editor Preferences 启用 Python Remote Execution)")
        sock.close()
        return None
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        sock.close()
        return None

if __name__ == "__main__":
    http_ok = test_remote_control_http()
    remote_py = test_python_remote_execution()
