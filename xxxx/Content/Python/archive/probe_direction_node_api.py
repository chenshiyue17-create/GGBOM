# -*- coding: utf-8 -*-
"""Read-only probe for graph actions needed by the direction-state rebuild."""
import json
from pathlib import Path

import unreal

root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
bp = unreal.load_asset("/Game/Blueprints/Player/BP_Player_Medic")
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
actions = [str(x) for x in editor.list_available_nodes([])]
wanted = [x for x in actions if any(k in x.lower() for k in ("sequence", "spawn actor", "normalize", "vector length", "just pressed"))]
(root / "output" / "direction_node_api_probe.json").write_text(
    json.dumps({"count": len(actions), "matches": wanted}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
