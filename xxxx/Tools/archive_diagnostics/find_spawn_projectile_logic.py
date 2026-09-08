import os
import sys
import json
import unreal

def log(msg):
    unreal.log(f"[FIND_SPAWN] {msg}")
    print(f"[FIND_SPAWN] {msg}")

def inspect_spawn_nodes():
    results = {}
    
    bps_to_check = [
        "/Game/Blueprints/Player/BP_Player_Medic",
        "/Game/Blueprints/Combat/Weapons/BP_WeaponBase",
        "/Game/Blueprints/Combat/Components/BPC_WeaponComponent",
        "/Game/Blueprints/Core/Components/BPC_WeaponInventory",
        "/Game/Blueprints/Projectiles/BP_Projectile_Base",
        "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
    ]
    
    for bp_path in bps_to_check:
        bp = unreal.EditorAssetLibrary.load_asset(bp_path)
        if not bp:
            continue
            
        graphs = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        bp_results = []
        
        # 遍历图表节点
        all_graphs = []
        # UBlueprint 在 UE Python 中有 uber_graph_pages 等或通过 function_graphs
        if hasattr(bp, "uber_graph_pages"):
            try:
                pages = bp.get_editor_property("uber_graph_pages")
                all_graphs.extend(pages)
            except Exception:
                pass
        if hasattr(bp, "function_graphs"):
            try:
                fgraphs = bp.get_editor_property("function_graphs")
                all_graphs.extend(fgraphs)
            except Exception:
                pass
                
        for g in all_graphs:
            g_name = g.get_name()
            nodes = g.get_editor_property("nodes") if hasattr(g, "nodes") else []
            for n in nodes:
                n_title = n.get_node_title(unreal.NodeTitleType.FULL_TITLE) if hasattr(n, "get_node_title") else str(n)
                n_class = n.get_class().get_name()
                
                # 检查是否为 SpawnActorFromClass 节点
                if "SpawnActor" in n_class or "SpawnActor" in str(n_title):
                    node_info = {
                        "graph": g_name,
                        "title": str(n_title),
                        "class": n_class,
                        "pins": []
                    }
                    if hasattr(n, "pins"):
                        for pin in n.get_editor_property("pins"):
                            pin_name = pin.get_editor_property("pin_name")
                            default_val = pin.get_editor_property("default_value") if hasattr(pin, "default_value") else ""
                            default_obj = pin.get_editor_property("default_object") if hasattr(pin, "default_object") else None
                            obj_name = default_obj.get_path_name() if default_obj else ""
                            node_info["pins"].append({
                                "name": str(pin_name),
                                "default_val": str(default_val),
                                "default_obj": obj_name
                            })
                    bp_results.append(node_info)
                    
        results[bp_path] = bp_results

    out_path = "/Users/cc/Desktop/GGBOM/xxxx/output/spawn_nodes_audit.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    log(f"Spawn 节点审计完成: {out_path}")

try:
    inspect_spawn_nodes()
except Exception as e:
    log(f"Inspect failed: {e}")
    sys.exit(1)
