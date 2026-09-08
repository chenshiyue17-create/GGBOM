import json
import unreal

world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/GGBOM/Maps/MAP_GGBOM_Main")
actors = unreal.EditorLevelLibrary.get_all_level_actors()

data = []
for a in actors:
    lbl = a.get_actor_label()
    cls = a.get_class().get_name()
    loc = a.get_actor_location()
    scale = a.get_actor_scale3d()
    comps = []
    for c in a.get_components_by_class(unreal.ActorComponent):
        col_prof = ""
        col_enabled = ""
        if isinstance(c, unreal.PrimitiveComponent):
            try:
                col_prof = str(c.get_collision_profile_name())
                col_enabled = str(c.get_collision_enabled())
            except Exception:
                pass
        comps.append({
            "name": c.get_name(),
            "class": c.__class__.__name__,
            "collision_profile": col_prof,
            "collision_enabled": col_enabled
        })
    data.append({
        "label": lbl,
        "class": cls,
        "location": [loc.x, loc.y, loc.z],
        "scale": [scale.x, scale.y, scale.z],
        "components": comps
    })

with open("/Users/cc/Desktop/GGBOM/xxxx/output/map_actors_list.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

unreal.log(f"Successfully dumped {len(data)} actors to map_actors_list.json")
