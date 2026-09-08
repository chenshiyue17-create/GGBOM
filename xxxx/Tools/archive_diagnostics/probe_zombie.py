# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/probe_zombie.txt"

bp = unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker")
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
nodes = ed.list_all_nodes()

lines = [f"Zombie Nodes Count: {len(nodes)}"]
for n in nodes:
    lines.append(f"Node: {n.get_name()} | Class: {n.get_class().get_name()} | Pos: ({n.get_node_pos().x}, {n.get_node_pos().y})")

# 尝试 add_event_override ReceiveAnyDamage
try:
    dmg_node = unreal.BlueprintEditorLibrary.add_event_override(bp, "ReceiveAnyDamage", unreal.IntPoint(0, 1000))
    if dmg_node:
        lines.append(f"SUCCESS added ReceiveAnyDamage: {dmg_node.get_name()}")
        out_pins = [unreal.BlueprintGraphPinLibrary.get_pin_name(p) for p in unreal.BlueprintEditorLibrary.list_output_pins(dmg_node)]
        lines.append(f"  Pins: {out_pins}")
    else:
        lines.append("ReceiveAnyDamage returned None")
except Exception as e:
    lines.append(f"EXCEPTION adding ReceiveAnyDamage: {e}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("PROBE_ZOMBIE_DONE")
