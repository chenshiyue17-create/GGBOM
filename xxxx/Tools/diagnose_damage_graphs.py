# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/diagnose_damage_graphs.txt"

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

bps = [
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound",
    "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
]

lines = []
for bp_path in bps:
    bp = ASSETS.load_asset(bp_path)
    lines.append(f"\n=== Blueprint: {bp_path} ===")
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for n in ed.list_all_nodes():
        title = BPLIB.get_node_title(n)
        pos = n.get_node_pos()
        if "Damage" in title or "Destroy" in title or "Health" in title or "Dead" in title or "Branch" in title:
            pins_info = []
            for p in BPLIB.list_all_pins(n):
                pname = PINLIB.get_pin_name(p)
                linked = len(PINLIB.get_pin_links(p)) > 0
                val = PINLIB.get_pin_default_value(p)
                if linked or (val and val != ""):
                    pins_info.append(f"{pname}(linked={linked}, val='{val}')")
            lines.append(f"  Node [{title}] at ({pos.x}, {pos.y}): {', '.join(pins_info)}")

OUT.write_text("\n".join(lines), encoding="utf-8")
