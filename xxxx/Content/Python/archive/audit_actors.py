# -*- coding: utf-8 -*-
from pathlib import Path
import unreal

map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
unreal.EditorLevelLibrary.load_level(map_path)
world = unreal.EditorLevelLibrary.get_editor_world()

actors = unreal.EditorLevelLibrary.get_all_level_actors()
out_file = Path("/Users/cc/Desktop/GGBOM/xxxx/Saved/Logs/ActorAudit.txt")
out_file.parent.mkdir(parents=True, exist_ok=True)

with open(out_file, "w", encoding="utf-8") as f:
    f.write(f"=== TOTAL ACTORS: {len(actors)} ===\n")
    for a in actors:
        loc = a.get_actor_location()
        f.write(f"Label: {a.get_actor_label()} | Class: {a.get_class().get_name()} | Pos: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})\n")

    # Inspect BP_Player_Medic Blueprint Subobjects
    bp = unreal.load_asset("/Game/GGBOM/Blueprints/BP_Player_Medic")
    f.write(f"\n=== BP_Player_Medic Subobjects ===\n")
    if bp:
        subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
        for h in handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
            f.write(f"Subobject: {obj.get_name() if obj else 'None'} | Class: {obj.get_class().get_name() if obj else 'None'}\n")
