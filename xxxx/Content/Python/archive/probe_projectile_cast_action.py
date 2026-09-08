import json
from pathlib import Path
import unreal

root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
bp = unreal.load_asset("/Game/Blueprints/Player/BP_Player_Medic")
projectile_class = unreal.load_class(None, "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C")
ed = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))
items = [str(x) for x in ed.list_available_nodes([])]
matches = [x for x in items if "projectile" in x.lower() or "投射" in x or ("castto" in x.lower() and "bp_" in x.lower())]
(root / "output" / "projectile_cast_action_probe.json").write_text(json.dumps({"class": projectile_class.get_path_name() if projectile_class else None, "matches": matches}, ensure_ascii=False, indent=2), encoding="utf-8")
