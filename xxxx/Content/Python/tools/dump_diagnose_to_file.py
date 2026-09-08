# -*- coding: utf-8 -*-
import unreal
import os

OUT_FILE = "/Users/cc/Desktop/GGBOM/diagnose_output.txt"
GEN = "/Game/GGBOM"
MAP_PATH = f"{GEN}/Maps/MAP_GGBOM_Main"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"

def run():
    lines = []
    lines.append("=== DUMP START ===")
    
    # 1. 检查玩家蓝图
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if bp:
        lines.append(f"Player BP: {bp.get_path_name()}")
        sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        handles = sub.k2_gather_subobject_data_for_blueprint(bp)
        for h in handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
            lines.append(f"Component: {vname} -> {type(obj).__name__}")
            if isinstance(obj, unreal.SceneComponent):
                loc = obj.get_editor_property("relative_location")
                rot = obj.get_editor_property("relative_rotation")
                scale = obj.get_editor_property("relative_scale3d")
                vis = obj.get_editor_property("visible")
                hidden = obj.get_editor_property("hidden_in_game")
                lines.append(f"  Loc={loc}, Rot={rot}, Scale={scale}, Vis={vis}, HiddenInGame={hidden}")
            if isinstance(obj, unreal.PaperFlipbookComponent):
                fb = obj.get_editor_property("source_flipbook")
                lines.append(f"  SourceFlipbook: {fb.get_path_name() if fb else 'None'}")
                trans = obj.get_editor_property("translucency_sort_priority")
                lines.append(f"  TranslucencySortPriority: {trans}")
            if isinstance(obj, unreal.PrimitiveComponent):
                try:
                    bi = obj.get_editor_property("body_instance")
                    lines.append(f"  CollisionProfile: {bi.get_editor_property('collision_profile_name')}, Enabled: {bi.get_editor_property('collision_enabled')}, SimPhys: {bi.get_editor_property('simulate_physics')}")
                except Exception as e:
                    lines.append(f"  Collision error: {e}")

    # 2. 检查关卡
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if world:
        lines.append("\n=== MAP ACTORS ===")
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        for a in actors:
            lbl = a.get_actor_label()
            cls = a.get_class().get_name()
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            scale = a.get_actor_scale3d()
            if any(k in lbl.lower() or k in cls.lower() for k in ["camera", "player", "start", "spawn"]):
                lines.append(f"Actor: {lbl} ({cls}) -> Loc={loc}, Rot={rot}, Scale={scale}")
                cam = a.get_component_by_class(unreal.CameraComponent)
                if cam:
                    proj = cam.get_editor_property("projection_mode")
                    fov = cam.get_editor_property("field_of_view")
                    ortho_w = cam.get_editor_property("ortho_width")
                    near_clip = cam.get_editor_property("ortho_near_clip_plane")
                    far_clip = cam.get_editor_property("ortho_far_clip_plane")
                    lines.append(f"  Camera ProjectionMode={proj}, FOV={fov}, OrthoWidth={ortho_w}, Near={near_clip}, Far={far_clip}")

        ws = world.get_world_settings()
        gm = ws.get_editor_property("default_game_mode")
        lines.append(f"\nDefaultGameMode: {gm.get_path_name() if gm else 'None'}")
        if gm:
            try:
                cdo_gm = unreal.get_default_object(gm)
                pawn_cls = cdo_gm.get_editor_property("default_pawn_class")
                lines.append(f"  DefaultPawnClass: {pawn_cls.get_path_name() if pawn_cls else 'None'}")
            except Exception as e:
                lines.append(f"  DefaultPawnClass error: {e}")

    lines.append("=== DUMP END ===")
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"DIAGNOSE_WRITTEN_TO_{OUT_FILE}")

if __name__ == "__main__":
    run()
