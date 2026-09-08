"""
Test ModelContextProtocol and Blueprint Combat Fix in running UE5.
"""
import unreal
import os
import json

def run():
    unreal.log("==================================================")
    unreal.log("🚀 [UNREAL MCP & COMBAT FIX] 开始执行自动化落实与验证...")
    unreal.log("==================================================")

    # 1. 尝试执行官方控制台命令
    world = unreal.EditorLevelLibrary.get_editor_world() if hasattr(unreal, "EditorLevelLibrary") else None
    
    mcp_results = {}
    commands = [
        "ModelContextProtocol.StartServer 8000",
        "ModelContextProtocol.GenerateClientConfig All",
        "ModelContextProtocol.RefreshTools"
    ]
    
    for cmd in commands:
        try:
            unreal.SystemLibrary.execute_console_command(world, cmd)
            mcp_results[cmd] = "executed"
            unreal.log(f"  ✅ 执行控制台命令: {cmd}")
        except Exception as e:
            mcp_results[cmd] = f"error: {e}"
            unreal.log(f"  ❌ 执行控制台命令失败 {cmd}: {e}")

    # 2. 检查 .mcp.json 是否生成
    proj_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
    mcp_json_path = os.path.join(proj_dir, ".mcp.json")
    mcp_results["mcp_json_exists"] = os.path.exists(mcp_json_path)
    if os.path.exists(mcp_json_path):
        try:
            with open(mcp_json_path, "r", encoding="utf-8") as f:
                mcp_results["mcp_json_content"] = json.load(f)
        except Exception as e:
            mcp_results["mcp_json_read_error"] = str(e)
            
    unreal.log(f"  📄 .mcp.json 状态: {mcp_results['mcp_json_exists']}")
    
    # 固化测试输出
    out_file = os.path.join(proj_dir, "output", "mcp_command_test_result.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(mcp_results, f, ensure_ascii=False, indent=2)
        
    unreal.log(f"  📄 结果报告已写入: {out_file}")

if __name__ == "__main__":
    run()
