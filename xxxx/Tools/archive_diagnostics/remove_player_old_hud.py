# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/inspect_player_hud_node.txt"

bp_path = "/Game/GGBOM/Blueprints/BP_GGBOM_Player"
bp = unreal.EditorAssetLibrary.load_asset(bp_path)
lines = []

if bp:
    lines.append(f"Loaded: {bp_path}")
    graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    nodes = ed.list_all_nodes() if ed else []
    lines.append(f"Total nodes in BP_GGBOM_Player: {len(nodes)}")
    for n in nodes:
        t = n.get_node_title(unreal.NodeTitleType.FULL_TITLE) if hasattr(n, "get_node_title") else str(n)
        lines.append(f"  Node: {t} [{n.get_class().get_name()}]")
        # 如果是 CreateWidget 节点，断开其连线或者移除它
        if "Create" in str(t) or "AddToViewport" in str(t):
            lines.append(f"    -> Found HUD node: {t}")
            for p in unreal.BlueprintEditorLibrary.list_all_pins(n):
                unreal.BlueprintGraphPinLibrary.break_pin_links(p)
            ed.remove_node(n)
            lines.append(f"    -> Removed node: {t}")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(bp)
    lines.append(f"Compiled and saved: {saved}")
else:
    lines.append("Not found")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
