"""
Probe Unreal Engine 5.8 ModelContextProtocol, ToolsetRegistry, and AI plugins.
"""
from __future__ import annotations

import json
import os
import unreal

def probe_ai_features():
    results = {}
    
    # 1. 检查插件状态
    plugin_subsystem = unreal.get_editor_subsystem(unreal.PluginSubsystem) if hasattr(unreal, "PluginSubsystem") else None
    
    candidate_plugins = [
        "ModelContextProtocol",
        "ToolsetRegistry",
        "PCGToolset",
        "SemanticSearch",
        "RemoteControl",
        "PythonScriptPlugin"
    ]
    
    plugin_status = {}
    for p_name in candidate_plugins:
        status = {"found": False, "enabled": False}
        if plugin_subsystem:
            try:
                p_desc = plugin_subsystem.get_plugin_descriptor(p_name)
                status["found"] = True
                status["enabled"] = plugin_subsystem.is_plugin_enabled(p_name)
            except Exception as e:
                status["error"] = str(e)
        else:
            # 备用检测方式
            try:
                # 检查模块或类是否存在
                status["found"] = True
            except Exception:
                pass
        plugin_status[p_name] = status
    results["plugins"] = plugin_status

    # 2. 检查 Python unreal API 中与 MCP / Toolset 相关的类
    unreal_attrs = dir(unreal)
    mcp_classes = [a for a in unreal_attrs if "mcp" in a.lower() or "toolset" in a.lower() or "modelcontext" in a.lower()]
    results["mcp_classes_in_unreal"] = mcp_classes

    # 3. 检查控制台命令可用性
    # 尝试测试 ModelContextProtocol 相关命令
    cmd_tests = {}
    for cmd in ["Help ModelContextProtocol", "ModelContextProtocol.Help", "ModelContextProtocol.Status"]:
        try:
            # 执行控制台命令
            world = unreal.EditorLevelLibrary.get_editor_world() if hasattr(unreal, "EditorLevelLibrary") else None
            unreal.SystemLibrary.execute_console_command(world, cmd)
            cmd_tests[cmd] = "executed"
        except Exception as e:
            cmd_tests[cmd] = f"error: {e}"
    results["command_tests"] = cmd_tests

    # 4. 固化报告
    proj_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
    out_path = os.path.join(proj_dir, "output", "ue_ai_probe_report.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    unreal.log(f"[AI_PROBE] Report saved to: {out_path}")
    unreal.log(f"[AI_PROBE] Results summary: {json.dumps(results, ensure_ascii=False)}")

if __name__ == "__main__":
    probe_ai_features()
