# -*- coding: utf-8 -*-
"""
全面校验 7 种敌人蓝图的动画、AI寻路、轴分离避障与碰撞体系
- 4 帧行尸家族：ZombieWalker, ZombieRunner, VenomShooter, ArmoredGuard, MutantBrute
- 完整动画怪物：MutantHound (4向Run + Pounce), Boss_Overlord (4向Walk + Ground_Slam)
"""
import json
import unreal

enemies = [
    "BP_Boss_Overlord",
    "BP_Enemy_MutantHound",
    "BP_Enemy_ZombieWalker",
    "BP_Enemy_ZombieRunner",
    "BP_Enemy_VenomShooter",
    "BP_Enemy_ArmoredGuard",
    "BP_Enemy_MutantBrute",
]

report = {}
subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

for name in enemies:
    bp_path = f"/Game/Blueprints/Characters/Enemies/{name}"
    bp = unreal.load_asset(bp_path)
    if not bp:
        report[name] = {"loaded": False}
        continue
    
    # 检查组件
    has_projectile_movement = False
    has_box_collision = False
    box_extent = None
    fb_name = None
    
    handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if isinstance(obj, unreal.ProjectileMovementComponent):
            has_projectile_movement = True
        elif isinstance(obj, unreal.BoxComponent):
            has_box_collision = True
            ext = obj.get_editor_property("box_extent")
            box_extent = [ext.x, ext.y, ext.z]
    
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        fb_comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
        if fb_comp:
            src = fb_comp.get_editor_property("source_flipbook")
            if src:
                fb_name = src.get_name()
    
    # 检查 EventGraph 中的追逐与轴分离
    graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    all_nodes = ed.list_all_nodes()
    
    has_get_player = any("GetPlayerPawn" in n.get_name() or "GetPlayerPawn" in str(n) for n in all_nodes)
    offset_nodes = [n for n in all_nodes if "K2_AddActorWorldOffset" in n.get_name() or "K2_AddActorWorldOffset" in str(n)]
    sweep_enabled_count = 0
    for node in offset_nodes:
        pins = unreal.BlueprintEditorLibrary.list_input_pins(node)
        for p in pins:
            if str(unreal.BlueprintGraphPinLibrary.get_pin_name(p)).lower() == "bsweep":
                val = unreal.BlueprintGraphPinLibrary.get_pin_default_value(p)
                if val.lower() == "true":
                    sweep_enabled_count += 1
    
    # 检查技能与分支
    branch_nodes = [n for n in all_nodes if "K2Node_IfThenElse" in n.get_class().get_name() or "Branch" in n.get_name()]
    
    is_zombie_family = "Zombie" in name or "Venom" in name or "Armored" in name or "Brute" in name
    
    report[name] = {
        "loaded": True,
        "is_zombie_4frame_family": is_zombie_family,
        "projectile_movement_removed": not has_projectile_movement,
        "has_pawn_box_collision": has_box_collision,
        "box_extent": box_extent,
        "source_flipbook": fb_name,
        "has_player_ai_chase": has_get_player,
        "sweep_offset_nodes_count": sweep_enabled_count,
        "branch_state_nodes_count": len(branch_nodes),
    }

out_path = "/Users/cc/Desktop/GGBOM/xxxx/output/ai_and_animation_audit.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"AUDIT_COMPLETE: Report written to {out_path}")
