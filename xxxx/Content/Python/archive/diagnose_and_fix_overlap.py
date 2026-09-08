# -*- coding: utf-8 -*-
import unreal
import sys

out_lines = []
def p(s):
    print(s)
    out_lines.append(str(s))

map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
unreal.EditorLevelLibrary.load_level(map_path)
world = unreal.EditorLevelLibrary.get_editor_world()

actors = unreal.EditorLevelLibrary.get_all_level_actors()
p(f"============================================================")
p(f"=== [ACTOR_LIST] TOTAL ACTORS IN MAP: {len(actors)} ===")
p(f"============================================================")
for a in actors:
    loc = a.get_actor_location()
    p(f"[ACTOR] Label: '{a.get_actor_label()}' | Class: {a.get_class().get_name()} | Pos: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")

# 检查所有可能的主角蓝图
for bp_p in [
    "/Game/Blueprints/Player/BP_Player_Medic",
    "/Game/GGBOM/Blueprints/BP_Player_Medic",
    "/Game/Blueprints/BP_Player_Medic"
]:
    if unreal.EditorAssetLibrary.does_asset_exist(bp_p):
        bp = unreal.load_asset(bp_p)
        cdo = unreal.get_default_object(bp.generated_class())
        p(f"------------------------------------------------------------")
        p(f"=== [BP FOUND] {bp_p} ===")
        p(f"AutoPossess: {cdo.get_editor_property('auto_possess_player')} | AutoReceiveInput: {cdo.get_editor_property('auto_receive_input')}")
        comps = cdo.get_components_by_class(unreal.ActorComponent)
        for comp in comps:
            p(f"  -> Comp: '{comp.get_name()}' | Class: {comp.get_class().get_name()}")

# 检查 GameMode
gm_path = "/Game/GGBOM/Blueprints/BP_GGBOM_GameMode"
if unreal.EditorAssetLibrary.does_asset_exist(gm_path):
    gm_bp = unreal.load_asset(gm_path)
    gm_cdo = unreal.get_default_object(gm_bp.generated_class())
    def_pawn = gm_cdo.get_editor_property("default_pawn_class")
    p(f"------------------------------------------------------------")
    p(f"=== [GAMEMODE] {gm_path} ===")
    p(f"DefaultPawnClass: {def_pawn.get_name() if def_pawn else 'None'}")

with open("/Users/cc/Desktop/GGBOM/xxxx/Content/Python/diagnose_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))
p("Saved to diagnose_output.txt")
