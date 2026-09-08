# -*- coding: utf-8 -*-
"""
deep_combat_diagnose.py
深度排查子弹与爆炸逻辑：
1. 检查 BP_ProjectileBase 当前的图表节点和所有连线
2. 检查 BP_ProjectileBase 的组件碰撞体属性（半径、通道响应、ObjectType）
3. 检查 BP_Combat_HitExplosion 的组件属性（Flipbook、Scale、LifeSpan）
4. 检查地图内怪物与玩家的 Location (X, Y, Z) 及碰撞体尺寸
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/deep_combat_diagnose.txt"

def run():
    lines = []
    lines.append("================ DEEP COMBAT DIAGNOSIS ================")
    
    ASSETS = unreal.EditorAssetLibrary
    BPLIB = unreal.BlueprintEditorLibrary
    PINLIB = unreal.BlueprintGraphPinLibrary

    # 1. 检查 BP_ProjectileBase
    proj_bp = ASSETS.load_asset("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
    if not proj_bp:
        lines.append("❌ 未能加载 BP_ProjectileBase")
    else:
        lines.append("--- BP_ProjectileBase CDO & Components ---")
        cdo = unreal.get_default_object(proj_bp.generated_class())
        subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        handles = subsys.k2_gather_subobject_data_for_blueprint(proj_bp)
        for h in handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, proj_bp)
            if not obj:
                continue
            lines.append(f"  Component: {vname} ({obj.get_class().get_name()})")
            if isinstance(obj, unreal.PrimitiveComponent):
                lines.append(f"    CollisionEnabled: {obj.get_collision_enabled()}")
                lines.append(f"    ObjectType: {obj.get_collision_object_type()}")
                lines.append(f"    GenOverlap: {obj.get_editor_property('generate_overlap_events')}")
                for ch in [unreal.CollisionChannel.ECC_WORLD_STATIC, unreal.CollisionChannel.ECC_WORLD_DYNAMIC, unreal.CollisionChannel.ECC_PAWN]:
                    lines.append(f"    Resp to {ch}: {obj.get_collision_response_to_channel(ch)}")
            if isinstance(obj, unreal.SphereComponent):
                lines.append(f"    SphereRadius: {obj.get_editor_property('sphere_radius')}")

        lines.append("\n--- BP_ProjectileBase EventGraph Nodes & Connections ---")
        graph = BPLIB.find_event_graph(proj_bp)
        ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        nodes = ed.list_all_nodes()
        lines.append(f"  Total Nodes: {len(nodes)}")
        for n in nodes:
            title = BPLIB.get_node_title(n)
            n_class = n.get_class().get_name()
            lines.append(f"  Node: [{n_class}] {title}")
            for p in BPLIB.list_output_pins(n):
                p_name = PINLIB.get_pin_name(p)
                p_type = PINLIB.get_pin_type(p)
                lines.append(f"    Pin out '{p_name}' (type={p_type})")

    # 2. 检查 BP_Combat_HitExplosion
    exp_bp = ASSETS.load_asset("/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion")
    if not exp_bp:
        lines.append("\n❌ 未能加载 BP_Combat_HitExplosion")
    else:
        lines.append("\n--- BP_Combat_HitExplosion ---")
        cdo_exp = unreal.get_default_object(exp_bp.generated_class())
        lines.append(f"  InitialLifeSpan: {cdo_exp.get_editor_property('initial_life_span')}")
        handles = subsys.k2_gather_subobject_data_for_blueprint(exp_bp)
        for h in handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, exp_bp)
            if not obj:
                continue
            lines.append(f"  Component: {vname} ({obj.get_class().get_name()})")
            if isinstance(obj, unreal.SceneComponent):
                lines.append(f"    RelativeScale3D: {obj.get_editor_property('relative_scale3d')}")
                lines.append(f"    Visible: {obj.get_editor_property('visible')}")
                lines.append(f"    HiddenInGame: {obj.get_editor_property('hidden_in_game')}")
            if isinstance(obj, unreal.PaperFlipbookComponent):
                fb = obj.get_editor_property("source_flipbook")
                lines.append(f"    SourceFlipbook: {fb.get_name() if fb else 'None'}")
                if fb:
                    lines.append(f"    TotalFrames: {fb.get_num_frames()}, TotalDuration: {fb.get_total_duration()}")

    # 3. 检查地图内怪物与玩家的 Location (X, Y, Z)
    world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/GGBOM/Maps/MAP_GGBOM_Main")
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    lines.append("\n--- MAP ACTORS TRANSFORM & COLLISION ---")
    for a in actors:
        lbl = a.get_actor_label()
        cname = a.get_class().get_name()
        if any(k in lbl.lower() or k in cname.lower() for k in ["player", "zombie", "hound", "boss"]):
            loc = a.get_actor_location()
            lines.append(f"  Actor: {lbl} ({cname}) @ Location: {loc}")
            for comp in a.get_components_by_class(unreal.ShapeComponent):
                c_lbl = comp.get_name()
                if isinstance(comp, unreal.BoxComponent):
                    ext = comp.get_editor_property("box_extent")
                    rloc = comp.get_editor_property("relative_location")
                    lines.append(f"    Shape: {c_lbl} BoxExtent={ext}, RelLoc={rloc}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ 诊断报告已写入 {OUT}", flush=True)

if __name__ == "__main__":
    run()
