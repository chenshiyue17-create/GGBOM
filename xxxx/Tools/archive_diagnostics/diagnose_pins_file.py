# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/diagnose_pins_and_collision.txt"

lines = []
lines.append("================ DIAGNOSE ================")

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

# 1. 检查 Branch 节点的引脚
proj_bp = unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
graph = BPLIB.find_event_graph(proj_bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
nodes = ed.list_all_nodes()

for n in nodes:
    title = str(BPLIB.get_node_title(n))
    cname = n.get_class().get_name()
    lines.append(f"Node: {title} ({cname})")
    in_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_input_pins(n)]
    out_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_output_pins(n)]
    lines.append(f"  Inputs: {in_pins}")
    lines.append(f"  Outputs: {out_pins}")

# 2. 检查子弹碰撞
handles = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem).k2_gather_subobject_data_for_blueprint(proj_bp)
for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, proj_bp)
    if isinstance(obj, unreal.SphereComponent):
        lines.append(f"SphereComponent: radius={obj.get_editor_property('sphere_radius')}")
        lines.append(f"  collision_enabled={obj.get_collision_enabled()}")
        lines.append(f"  object_type={obj.get_collision_object_type()}")
        lines.append(f"  response_pawn={obj.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)}")
        lines.append(f"  response_world_dyn={obj.get_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC)}")

OUT.write_text("\n".join(lines), encoding="utf-8")
unreal.log("✅ DIAGNOSE SAVED")
