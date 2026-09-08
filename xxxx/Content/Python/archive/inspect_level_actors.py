# -*- coding: utf-8 -*-
import unreal

map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
unreal.EditorLevelLibrary.load_level(map_path)
world = unreal.EditorLevelLibrary.get_editor_world()

actors = unreal.EditorLevelLibrary.get_all_level_actors()
unreal.log(f"=== [ACTOR_LIST] TOTAL ACTORS IN MAP: {len(actors)} ===")
for a in actors:
    loc = a.get_actor_location()
    unreal.log(f"[ACTOR_ITEM] Label: {a.get_actor_label()} | Class: {a.get_class().get_name()} | Pos: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")

# Check BP_Player_Medic components
bp = unreal.load_asset("/Game/GGBOM/Blueprints/BP_Player_Medic")
cdo = unreal.get_default_object(bp.generated_class())
unreal.log(f"=== [BP_PLAYER_MEDIC CDO] ===")
for comp in cdo.get_components_by_class(unreal.ActorComponent):
    unreal.log(f"[CDO_COMP] Name: {comp.get_name()} | Class: {comp.get_class().get_name()}")
