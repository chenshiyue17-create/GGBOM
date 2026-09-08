"""
Diagnose blueprint compilation errors for key blueprints in GGBOM.
"""
from __future__ import annotations

import unreal
import json
import os

BLUEPRINTS_TO_CHECK = [
    "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase",
    "/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion",
    "/Game/Blueprints/Player/BP_Player_Medic",
    "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord",
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
    "/Game/GGBOM/Blueprints/BP_StageWaveManager_Live",
    "/Game/GGBOM/Blueprints/BP_GGBOM_GameMode"
]

def check_blueprints():
    results = {}
    unreal.log("==================================================")
    unreal.log("🔍 开始全量诊断蓝图编译错误与警告...")
    
    for bp_path in BLUEPRINTS_TO_CHECK:
        bp = unreal.EditorAssetLibrary.load_asset(bp_path)
        if not bp:
            results[bp_path] = {"loaded": False, "error": "Asset not found"}
            continue
            
        # 获取图表编辑器以检查消息
        graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        nodes_info = []
        errors = []
        warnings = []
        
        if graph:
            ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
            if ed:
                # 编译
                unreal.BlueprintEditorLibrary.compile_blueprint(bp)
                
                # 检查警告与错误节点
                warn_nodes = ed.list_nodes_with_warnings()
                note_nodes = ed.list_nodes_with_notes()
                all_nodes = ed.list_all_nodes()
                
                for n in warn_nodes:
                    warnings.append(f"{n.get_name()} ({type(n).__name__})")
                    
                for n in all_nodes:
                    nodes_info.append(f"{n.get_name()}: {type(n).__name__}")
                    
        # 检查蓝图状态
        status = str(bp.get_editor_property("status")) if hasattr(bp, "get_editor_property") else "Unknown"
        
        results[bp_path] = {
            "loaded": True,
            "status": status,
            "node_count": len(nodes_info),
            "warnings": warnings,
            "nodes": nodes_info
        }
        unreal.log(f"  📦 [{bp_path}] 状态: {status} | 节点数: {len(nodes_info)} | 警告数: {len(warnings)}")

    # 固化报告
    proj_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
    out_file = os.path.join(proj_dir, "output", "blueprint_compilation_diagnosis.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    unreal.log(f"📄 诊断报告已固化至: {out_file}")
    unreal.log("==================================================")

if __name__ == "__main__":
    check_blueprints()
