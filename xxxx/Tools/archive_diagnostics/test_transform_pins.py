# -*- coding: utf-8 -*-
import unreal

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

proj_bp = ASSETS.load_asset("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
graph = BPLIB.find_event_graph(proj_bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

from pathlib import Path
ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/test_transform_pins.txt"
lines = []

for fn in [
    "/Script/Engine.Actor.GetTransform",
    "/Script/Engine.Actor.K2_GetActorTransform",
    "/Script/Engine.GameplayStatics.GetActorTransform",
    "/Script/Engine.KismetMathLibrary.MakeTransform"
]:
    node = ed.add_call_function_node(fn)
    if node:
        lines.append(f"✅ 找到函数: {fn} -> 节点: {BPLIB.get_node_title(node)}")
        for p in BPLIB.list_input_pins(node):
            lines.append(f"   InPin: {PINLIB.get_pin_name(p)}")
        for p in BPLIB.list_output_pins(node):
            lines.append(f"   OutPin: {PINLIB.get_pin_name(p)}")
        ed.remove_nodes([node])
    else:
        lines.append(f"❌ 未找到: {fn}")

OUT.write_text("\n".join(lines), encoding="utf-8")
