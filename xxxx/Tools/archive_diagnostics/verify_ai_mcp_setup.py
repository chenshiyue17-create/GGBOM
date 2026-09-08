#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
verify_ai_mcp_setup.py
虚幻引擎 5.8 官方 Unreal MCP / AI 全量配置与连通性自检工具
================================================================================
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from pathlib import Path

WORKSPACE_ROOT = Path("/Users/cc/Desktop/GGBOM")
PROJECT_ROOT = WORKSPACE_ROOT / "xxxx"

def check_file_exists(path: Path) -> dict:
    return {
        "path": str(path),
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else 0
    }

def check_uproject():
    uproj_path = PROJECT_ROOT / "xxxx.uproject"
    if not uproj_path.exists():
        return {"status": "FAIL", "reason": "uproject not found"}
    data = json.loads(uproj_path.read_text(encoding="utf-8"))
    plugins = {p["Name"]: p.get("Enabled", False) for p in data.get("Plugins", [])}
    reqs = ["ModelContextProtocol", "ToolsetRegistry", "AllToolsets", "RemoteControl"]
    details = {r: plugins.get(r, False) for r in reqs}
    all_ok = all(details.values())
    return {
        "status": "PASS" if all_ok else "PARTIAL",
        "plugins": details
    }

def check_ini_settings():
    ini_path = PROJECT_ROOT / "Config" / "DefaultEditorPerProjectUserSettings.ini"
    engine_ini = PROJECT_ROOT / "Config" / "DefaultEngine.ini"
    
    found_user = False
    if ini_path.exists():
        txt = ini_path.read_text(encoding="utf-8")
        found_user = "ModelContextProtocolSettings" in txt and "bAutoStartServer=True" in txt
        
    found_engine = False
    if engine_ini.exists():
        txt = engine_ini.read_text(encoding="utf-8")
        found_engine = "ModelContextProtocolSettings" in txt and "bAutoStartServer=True" in txt
        
    return {
        "DefaultEditorPerProjectUserSettings.ini": {"exists": ini_path.exists(), "configured": found_user},
        "DefaultEngine.ini": {"exists": engine_ini.exists(), "configured": found_engine},
        "status": "PASS" if (found_user or found_engine) else "FAIL"
    }

def check_mcp_configs():
    cfgs = [
        WORKSPACE_ROOT / ".mcp.json",
        PROJECT_ROOT / ".mcp.json",
        WORKSPACE_ROOT / ".agents" / "mcp_config.json",
        PROJECT_ROOT / ".agents" / "mcp_config.json"
    ]
    results = {}
    for c in cfgs:
        results[str(c.relative_to(WORKSPACE_ROOT))] = {
            "exists": c.exists(),
            "valid_json": False
        }
        if c.exists():
            try:
                json.loads(c.read_text(encoding="utf-8"))
                results[str(c.relative_to(WORKSPACE_ROOT))]["valid_json"] = True
            except Exception:
                pass
    all_valid = all(v["exists"] and v["valid_json"] for v in results.values())
    return {
        "status": "PASS" if all_valid else "WARN",
        "configs": results
    }

def check_bridge_script():
    bridge_path = PROJECT_ROOT / "Tools" / "unreal_mcp_bridge.py"
    if not bridge_path.exists():
        return {"status": "FAIL", "reason": "unreal_mcp_bridge.py not found"}
    # 模拟 stdin 发送 initialize 请求
    try:
        proc = subprocess.Popen(
            ["python3", str(bridge_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        out, err = proc.communicate(input='{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}\n', timeout=3.0)
        resp = json.loads(out.strip())
        is_ok = "result" in resp and resp["result"]["serverInfo"]["name"] == "unreal-mcp-bridge"
        return {
            "status": "PASS" if is_ok else "FAIL",
            "server_info": resp.get("result", {}).get("serverInfo", {})
        }
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}

def check_ports():
    ports = {}
    # 30010 RemoteControl
    try:
        req = urllib.request.Request("http://127.0.0.1:30010/remote/info")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            ports["30010_RemoteControl"] = {"online": True, "routes": len(data.get("HttpRoutes", []))}
    except Exception as e:
        ports["30010_RemoteControl"] = {"online": False, "error": str(e)}
        
    # 8000 Official MCP
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/mcp")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            ports["8000_OfficialMCP"] = {"online": True, "status": resp.status}
    except Exception as e:
        ports["8000_OfficialMCP"] = {"online": False, "notice": "将在虚幻编辑器启动或执行 ModelContextProtocol.StartServer 后就绪"}
        
    return ports

def main():
    report = {
        "title": "Unreal Engine 5.8 官方 AI / MCP 全量配置与通信自检报告",
        "uproject_plugins": check_uproject(),
        "ini_autostart_settings": check_ini_settings(),
        "client_mcp_configs": check_mcp_configs(),
        "mcp_stdio_bridge": check_bridge_script(),
        "live_ports": check_ports()
    }
    
    out_file = PROJECT_ROOT / "output" / "ai_mcp_setup_verification.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print("==================================================")
    print("📋 [AI / MCP 配置检测报告]")
    print(f"  - 插件配置 (.uproject)          : {report['uproject_plugins']['status']}")
    print(f"  - 自动启动配置 (INI)            : {report['ini_autostart_settings']['status']}")
    print(f"  - 客户端配置 (.mcp.json)        : {report['client_mcp_configs']['status']}")
    print(f"  - MCP Stdio 桥接器              : {report['mcp_stdio_bridge']['status']}")
    print(f"  - 虚幻引擎 30010 实时端口       : {'🟢 在线' if report['live_ports']['30010_RemoteControl']['online'] else '🔴 离线'}")
    print(f"  - 虚幻引擎 8000 官方 MCP 端口   : {'🟢 在线' if report['live_ports']['8000_OfficialMCP']['online'] else '🟡 待拉起'}")
    print("==================================================")
    print(f"📄 详细 JSON 报告已固化至: {out_file}")

if __name__ == "__main__":
    main()
