# -*- coding: utf-8 -*-
"""
inspect_ai_movement.py
检查敌人（Zombie, Hound, Boss）和主角（Player）的当前移动蓝图图表与碰撞配置
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/ai_movement_inspect.txt"

def run():
    ASSETS = unreal.EditorAssetLibrary
    BPLIB = unreal.BlueprintEditorLibrary
    PINLIB = unreal.BlueprintGraphPinLibrary

    lines = []
    lines.append("================ AI MOVEMENT & COLLISION AUDIT ================")

    bps = [
        ("Player", "/Game/Blueprints/Player/BP_Player_Medic"),
        ("Zombie", "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"),
        ("Hound", "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"),
        ("Boss", "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"),
    ]

    for label, path in bps:
        lines.append(f"\n--- {label}: {path} ---")
        bp = ASSETS.load_asset(path)
        if not bp:
            lines.append("  ❌ 资产不存在")
            continue
        
        # 1. 组件碰撞
        cdo = unreal.get_default_object(bp.generated_class())
        subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
        for h in handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
            if not obj or not isinstance(obj, unreal.PrimitiveComponent):
                continue
            lines.append(f"  Comp: {vname} ({obj.get_class().get_name()})")
            lines.append(f"    Profile: {obj.get_collision_profile_name()}")
            lines.append(f"    Enabled: {obj.get_collision_enabled()}")
            lines.append(f"    ObjectType: {obj.get_collision_object_type()}")
            lines.append(f"    Resp Pawn: {obj.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)}")
            lines.append(f"    Resp WorldDyn: {obj.get_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC)}")
            if isinstance(obj, unreal.BoxComponent):
                lines.append(f"    BoxExtent: {obj.get_editor_property('box_extent')}")
            elif isinstance(obj, unreal.CapsuleComponent):
                lines.append(f"    CapsuleRadius: {obj.get_editor_property('capsule_radius')}, HalfHeight: {obj.get_editor_property('capsule_half_height')}")

        # 2. EventGraph 节点简要
        graph = BPLIB.find_event_graph(bp)
        if graph:
            ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
            nodes = ed.list_all_nodes()
            lines.append(f"  Graph Nodes Total: {len(nodes)}")
            for n in nodes:
                title = BPLIB.get_node_title(n)
                lines.append(f"    Node: [{n.get_class().get_name()}] {title}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ AI移动与碰撞审查结果已输出至 {OUT}", flush=True)

if __name__ == "__main__":
    run()
