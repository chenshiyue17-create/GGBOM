#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
unreal_mcp_bridge.py
虚幻引擎 5.8 官方 MCP 与 Remote Control 双模桥接服务器
提供标准 MCP (Model Context Protocol) JSON-RPC Stdio 接口
支持与 Antigravity、Claude Code、Cursor 无缝连接
================================================================================
"""
from __future__ import annotations

import json
import sys
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Dict, List

RC_URL = "http://127.0.0.1:30010"
OFFICIAL_MCP_URL = "http://127.0.0.1:8000/mcp"

def send_rc_request(endpoint: str, method: str = "GET", payload: Dict[str, Any] = None) -> Dict[str, Any]:
    url = f"{RC_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Content-Type": "application/json"} if payload else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        return {"error": f"HTTP {e.code}: {e.reason}", "detail": err_body}
    except Exception as e:
        return {"error": str(e)}

def check_official_mcp() -> Dict[str, Any]:
    try:
        req = urllib.request.Request(OFFICIAL_MCP_URL, method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return {"online": True, "status": resp.status, "url": OFFICIAL_MCP_URL}
    except Exception as e:
        return {"online": False, "error": str(e), "url": OFFICIAL_MCP_URL}

TOOLS_DEFINITIONS = [
    {
        "name": "ue_mcp_status",
        "description": "检查虚幻引擎官方 ModelContextProtocol (8000端口) 与 Remote Control (30010端口) 的运行状态",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "ue_read_property",
        "description": "通过 Remote Control 读取虚幻引擎中指定对象或 Actor 的属性值",
        "inputSchema": {
            "type": "object",
            "properties": {
                "objectPath": {"type": "string", "description": "对象的完整路径或类路径，例如 /Game/GGBOM/Maps/MAP_GGBOM_Main.MAP_GGBOM_Main:PersistentLevel.PlayerStart"},
                "propertyName": {"type": "string", "description": "要读取的属性名称"}
            },
            "required": ["objectPath", "propertyName"]
        }
    },
    {
        "name": "ue_write_property",
        "description": "通过 Remote Control 设置虚幻引擎中指定对象的属性值",
        "inputSchema": {
            "type": "object",
            "properties": {
                "objectPath": {"type": "string", "description": "对象的完整路径"},
                "propertyName": {"type": "string", "description": "要设置的属性名称"},
                "propertyValue": {"description": "新的属性值 (基础类型、对象或字典)"}
            },
            "required": ["objectPath", "propertyName", "propertyValue"]
        }
    },
    {
        "name": "ue_describe_object",
        "description": "获取虚幻引擎中指定对象的所有公开属性、函数和元数据定义",
        "inputSchema": {
            "type": "object",
            "properties": {
                "objectPath": {"type": "string", "description": "对象的完整路径"}
            },
            "required": ["objectPath"]
        }
    },
    {
        "name": "ue_search_assets",
        "description": "在虚幻引擎工程中搜索资产",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "packageNames": {"type": "array", "items": {"type": "string"}, "description": "限定包路径，例如 ['/Game/Blueprints']"}
            },
            "required": ["query"]
        }
    }
]

def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Any:
    if name == "ue_mcp_status":
        rc_info = send_rc_request("/remote/info")
        official_mcp = check_official_mcp()
        return {
            "official_mcp_server": official_mcp,
            "remote_control_server": {
                "online": "error" not in rc_info,
                "routes_count": len(rc_info.get("HttpRoutes", [])) if "HttpRoutes" in rc_info else 0
            }
        }
    elif name == "ue_read_property":
        obj_path = arguments.get("objectPath")
        prop_name = arguments.get("propertyName")
        payload = {"objectPath": obj_path, "propertyName": prop_name, "access": "READ_ACCESS"}
        return send_rc_request("/remote/object/property", method="PUT", payload=payload)
    elif name == "ue_write_property":
        obj_path = arguments.get("objectPath")
        prop_name = arguments.get("propertyName")
        val = arguments.get("propertyValue")
        payload = {"objectPath": obj_path, "propertyName": prop_name, "propertyValue": val, "access": "WRITE_ACCESS"}
        return send_rc_request("/remote/object/property", method="PUT", payload=payload)
    elif name == "ue_describe_object":
        obj_path = arguments.get("objectPath")
        payload = {"objectPath": obj_path}
        return send_rc_request("/remote/object/describe", method="PUT", payload=payload)
    elif name == "ue_search_assets":
        query = arguments.get("query")
        pkgs = arguments.get("packageNames", [])
        payload = {"query": query, "packageNames": pkgs}
        return send_rc_request("/remote/search/assets", method="PUT", payload=payload)
    else:
        return {"error": f"Unknown tool: {name}"}

def process_message(msg: Dict[str, Any]) -> Dict[str, Any] | None:
    msg_id = msg.get("id")
    method = msg.get("method")
    params = msg.get("params", {})
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "unreal-mcp-bridge",
                    "version": "1.0.0"
                }
            }
        }
    elif method == "notifications/initialized":
        return None
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": TOOLS_DEFINITIONS
            }
        }
    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        res = handle_tool_call(tool_name, args)
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(res, ensure_ascii=False, indent=2)
                    }
                ]
            }
        }
    elif method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {}
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = process_message(req)
            if resp:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
