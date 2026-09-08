# -*- coding: utf-8 -*-
import unreal

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary

for name in ["BP_Enemy_MutantHound", "BP_Enemy_ZombieWalker"]:
    p = f"/Game/Blueprints/Characters/Enemies/{name}"
    bp = ASSETS.load_asset(p)
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick = ed.find_event_node("ReceiveTick")
    print(f"BP {name}: graph={graph is not None}, tick={tick is not None}")

from pathlib import Path
ROOT = Path(unreal.Paths.project_dir()).resolve()
(ROOT / "output/check_hound_zombie_tick.txt").write_text("Checked", encoding="utf-8")
