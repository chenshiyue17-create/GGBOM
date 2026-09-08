# -*- coding: utf-8 -*-
import unreal
import json
from pathlib import Path

map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
unreal.EditorLevelLibrary.load_level(map_path)

actors = unreal.EditorLevelLibrary.get_all_level_actors()
results = []
for a in actors:
    cname = a.get_class().get_name()
    label = a.get_actor_label() if hasattr(a, "get_actor_label") else a.get_name()
    if any(k in cname.lower() or k in label.lower() for k in ["zombie", "hound", "boss", "player"]):
        loc = a.get_actor_location()
        results.append({
            "name": a.get_name(),
            "label": label,
            "class": cname,
            "loc": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)]
        })

out = Path(unreal.Paths.project_dir()).resolve() / "output/enemy_positions.json"
out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Exported {len(results)} actors to {out}")
