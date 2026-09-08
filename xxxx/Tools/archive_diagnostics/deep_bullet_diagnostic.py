# -*- coding: utf-8 -*-
import json
import os
import unreal

def diagnose():
    report = {}
    
    # 1. 检查 BP_ProjectileBase
    bp_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    if not bp:
        print(f"FAILED: Cannot load {bp_path}")
        return
        
    cdo = unreal.get_default_object(bp.generated_class())
    report["BP_ProjectileBase"] = {
        "cdo_initial_life_span": getattr(cdo, "initial_life_span", None),
        "components": [],
        "graph_nodes": []
    }
    
    subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for h in subsys.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if obj:
            c_info = {
                "var_name": vname,
                "class": obj.get_class().get_name(),
            }
            if isinstance(obj, unreal.PrimitiveComponent):
                try:
                    c_info["collision_enabled"] = str(obj.get_collision_enabled())
                except Exception:
                    pass
                try:
                    c_info["collision_profile_name"] = str(obj.get_collision_profile_name())
                except Exception:
                    pass
                try:
                    c_info["generate_overlap_events"] = bool(obj.get_editor_property("b_generate_overlap_events"))
                except Exception:
                    try:
                        c_info["generate_overlap_events"] = bool(obj.get_generate_overlap_events())
                    except Exception:
                        pass
                try:
                    c_info["notify_rigid_body_collision"] = bool(obj.get_editor_property("notify_rigid_body_collision"))
                except Exception:
                    pass
                try:
                    c_info["object_type"] = str(obj.get_collision_object_type())
                except Exception:
                    pass
                # 检查主要通道
                responses = {}
                for ch in [unreal.CollisionChannel.ECC_WORLD_STATIC,
                           unreal.CollisionChannel.ECC_WORLD_DYNAMIC,
                           unreal.CollisionChannel.ECC_PAWN,
                           unreal.CollisionChannel.ECC_VISIBILITY,
                           unreal.CollisionChannel.ECC_CAMERA]:
                    responses[str(ch)] = str(obj.get_collision_response_to_channel(ch))
                c_info["responses"] = responses
            if isinstance(obj, unreal.ProjectileMovementComponent):
                c_info["initial_speed"] = float(obj.initial_speed)
                c_info["max_speed"] = float(obj.max_speed)
                c_info["gravity_scale"] = float(obj.projectile_gravity_scale)
            report["BP_ProjectileBase"]["components"].append(c_info)
            
    # 图表节点与连线检查
    graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    if graph:
        ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        nodes = ed.list_all_nodes()
        for n in nodes:
            n_name = n.get_name()
            n_title = str(unreal.BlueprintEditorLibrary.get_node_title(n))
            n_cls = n.get_class().get_name()
            input_pins = set(unreal.BlueprintEditorLibrary.list_input_pins(n))
            pins_info = []
            for p in unreal.BlueprintEditorLibrary.list_all_pins(n):
                p_name = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
                p_dir = "In" if p in input_pins else "Out"
                p_val = ""
                try:
                    p_val = unreal.BlueprintGraphPinLibrary.get_pin_value(p)
                except Exception:
                    pass
                # 检查连接的目标
                linked_pins = []
                # BlueprintGraphPinLibrary doesn't have direct get_linked_pins in some UE versions, but let's check
                pins_info.append(f"{p_dir}:{p_name}={p_val}")
            report["BP_ProjectileBase"]["graph_nodes"].append({
                "name": n_name,
                "title": n_title,
                "class": n_cls,
                "pins": pins_info
            })

    # 2. 检查怪物受击碰撞 BP_Enemy_ZombieWalker
    zombie_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
    zombie_bp = unreal.EditorAssetLibrary.load_asset(zombie_path)
    if zombie_bp:
        report["BP_Enemy_ZombieWalker"] = {"components": []}
        for h in subsys.k2_gather_subobject_data_for_blueprint(zombie_bp):
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, zombie_bp)
            if obj and isinstance(obj, unreal.PrimitiveComponent):
                c_info = {
                    "var_name": vname,
                    "class": obj.get_class().get_name(),
                }
                try:
                    c_info["collision_enabled"] = str(obj.get_collision_enabled())
                except Exception:
                    pass
                try:
                    c_info["collision_profile_name"] = str(obj.get_collision_profile_name())
                except Exception:
                    pass
                try:
                    c_info["generate_overlap_events"] = bool(obj.get_editor_property("b_generate_overlap_events"))
                except Exception:
                    try:
                        c_info["generate_overlap_events"] = bool(obj.get_generate_overlap_events())
                    except Exception:
                        pass
                try:
                    c_info["object_type"] = str(obj.get_collision_object_type())
                except Exception:
                    pass
                responses = {}
                for ch in [unreal.CollisionChannel.ECC_WORLD_STATIC,
                           unreal.CollisionChannel.ECC_WORLD_DYNAMIC,
                           unreal.CollisionChannel.ECC_PAWN]:
                    responses[str(ch)] = str(obj.get_collision_response_to_channel(ch))
                c_info["responses"] = responses
                if isinstance(obj, unreal.BoxComponent):
                    c_info["box_extent"] = str(obj.get_editor_property("box_extent"))
                report["BP_Enemy_ZombieWalker"]["components"].append(c_info)

    out_file = "/Users/cc/Desktop/GGBOM/xxxx/output/deep_bullet_diagnostic.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Deep diagnostic saved to {out_file}")

if __name__ == "__main__":
    diagnose()
