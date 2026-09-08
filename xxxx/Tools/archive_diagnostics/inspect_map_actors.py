import os
import sys
import json
import unreal

def inspect_map():
    map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
    # 加载关卡
    success = unreal.EditorLevelLibrary.load_level(map_path)
    if not success:
        print(f"Failed to load map: {map_path}")
        return
        
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    actor_list = []
    for a in actors:
        actor_list.append({
            "name": a.get_name(),
            "class": a.get_class().get_name(),
            "label": a.get_actor_label() if hasattr(a, "get_actor_label") else ""
        })
        
    out_path = "/Users/cc/Desktop/GGBOM/xxxx/output/map_actors_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"total": len(actor_list), "actors": actor_list}, f, ensure_ascii=False, indent=2)
        
    print(f"Map actors exported to {out_path}, count: {len(actor_list)}")

try:
    inspect_map()
except Exception as e:
    print(f"Error: {e}")
