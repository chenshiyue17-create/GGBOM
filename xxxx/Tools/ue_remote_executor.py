# -*- coding: utf-8 -*-
"""
================================================================================
ue_remote_executor.py
UE5 Python Remote Execution 官方标准协议客户端 (macOS 深度优化版)
实现外部 AI 与运行中的 Unreal Editor 实时通信与代码执行
================================================================================
"""
import sys
import socket
import json
import time
import struct
import platform

class UERemoteExecution:
    PROTOCOL_VERSION = 1
    PROTOCOL_MAGIC = "ue_py"
    
    TYPE_OPEN_CONNECTION = "open_connection"
    TYPE_OPENED_CONNECTION = "opened_connection"
    TYPE_COMMAND = "command"
    TYPE_COMMAND_RESULT = "command_result"
    TYPE_CLOSE_CONNECTION = "close_connection"
    
    EXEC_MODE_STATEMENT = "ExecuteStatement"
    EXEC_MODE_FILE = "ExecuteFile"
    
    def __init__(self, multicast_group="239.0.0.1", multicast_port=6766):
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port
        self.udp_sock = None
        self.tcp_sock = None
        self.connected_node = None
        
    def _create_udp_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.settimeout(2.5)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except Exception:
                pass
                
        # 允许组播广播与本地回环
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        except Exception:
            pass
            
        sock.bind(("", 0))
        return sock

    def connect(self):
        print(f"📡 [RemoteExec] 正在向 UE5 发起握手探测 (组播 {self.multicast_group}:{self.multicast_port})...")
        self.udp_sock = self._create_udp_socket()
        
        req = {
            "version": self.PROTOCOL_VERSION,
            "magic": self.PROTOCOL_MAGIC,
            "type": self.TYPE_OPEN_CONNECTION,
            "source": "antigravity"
        }
        msg = json.dumps(req).encode("utf-8")
        
        # 探测目标列表: 组播地址、本地广播、本地单播
        targets = [
            (self.multicast_group, self.multicast_port),
            ("127.0.0.1", self.multicast_port),
            ("255.255.255.255", self.multicast_port)
        ]
        
        # 在 macOS 上尝试绑定回环接口多播
        if platform.system() == "Darwin":
            try:
                self.udp_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton("127.0.0.1"))
            except Exception:
                pass
                
        for t in targets:
            try:
                self.udp_sock.sendto(msg, t)
            except Exception as e:
                pass

        # 等待 UE5 编辑器响应
        start_t = time.time()
        tcp_info = None
        while time.time() - start_t < 3.0:
            try:
                data, addr = self.udp_sock.recvfrom(65535)
                payload = json.loads(data.decode("utf-8"))
                if payload.get("magic") == self.PROTOCOL_MAGIC and payload.get("type") == self.TYPE_OPENED_CONNECTION:
                    tcp_info = payload.get("data", {}).get("command_connection")
                    self.connected_node = payload.get("data", {}).get("node")
                    print(f"🎉 [RemoteExec] 成功连通 UE5 编辑器节点 [{self.connected_node}]！")
                    print(f"   TCP 端口: {tcp_info}")
                    break
            except socket.timeout:
                break
            except Exception as e:
                pass

        if not tcp_info:
            print("❌ [RemoteExec] 未能与 UE5 建立握手。")
            return False

        # 建立 TCP 命令连接
        tcp_ip = tcp_info.get("ip", "127.0.0.1")
        tcp_port = tcp_info.get("port")
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.settimeout(10.0)
        self.tcp_sock.connect((tcp_ip, tcp_port))
        print("🔗 [RemoteExec] TCP 命令通道已建立！可实时执行代码！")
        return True

    def run_command(self, cmd_str, exec_mode="ExecuteStatement"):
        if not self.tcp_sock:
            raise RuntimeError("TCP 未连接！")
            
        req = {
            "version": self.PROTOCOL_VERSION,
            "magic": self.PROTOCOL_MAGIC,
            "type": self.TYPE_COMMAND,
            "data": {
                "command": cmd_str,
                "exec_mode": exec_mode
            }
        }
        raw = json.dumps(req).encode("utf-8")
        self.tcp_sock.sendall(raw)
        
        # 接收响应
        buffer = b""
        start_t = time.time()
        while time.time() - start_t < 15.0:
            try:
                chunk = self.tcp_sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk
                try:
                    res = json.loads(buffer.decode("utf-8"))
                    if res.get("type") == self.TYPE_COMMAND_RESULT:
                        output_list = res.get("data", {}).get("output", [])
                        for item in output_list:
                            print(f"[UE_OUTPUT] {item.get('output', '')}", end="")
                        return res.get("data")
                except json.JSONDecodeError:
                    continue
            except socket.timeout:
                break
                
        return None

    def close(self):
        if self.tcp_sock:
            try:
                req = {
                    "version": self.PROTOCOL_VERSION,
                    "magic": self.PROTOCOL_MAGIC,
                    "type": self.TYPE_CLOSE_CONNECTION
                }
                self.tcp_sock.sendall(json.dumps(req).encode("utf-8"))
                self.tcp_sock.close()
            except Exception:
                pass
        if self.udp_sock:
            try: self.udp_sock.close()
            except Exception: pass
        print("🔌 [RemoteExec] 连接已关闭。")

if __name__ == "__main__":
    client = UERemoteExecution()
    if client.connect():
        print("🚀 发送热更新代码至 UE5...")
        client.run_command("import hot_reload; hot_reload.hot_reload_all()")
        client.close()
    else:
        sys.exit(1)
