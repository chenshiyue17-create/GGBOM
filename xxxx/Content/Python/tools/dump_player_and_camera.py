# -*- coding: utf-8 -*-
import unreal

GEN = "/Game/GGBOM"
MAP_PATH = f"{GEN}/Maps/MAP_GGBOM_Main"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"

def dump_all():
    print("=== DUMPING PLAYER BP ===")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if bp:
        gen_class = bp.generated_class()
        print(f"Generated Class: {gen_class.get_name() if gen_class else 'None'}")
        if gen_class:
            cdo = unreal.get_default_object(gen_class)
            print(f"CDO: {cdo}")

        sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        handles = sub.k2_gather_subobject_data_for_blueprint(bp)
        for h in handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
            print(f"Component: {vname} -> {type(obj).__name__}", flush=True)
            if isinstance(obj, unreal.SceneComponent):
                loc = obj.get_editor_property("relative_location")
                rot = obj.get_editor_property("relative_rotation")
                scale = obj.get_editor_property("relative_scale3d")
                vis = obj.get_editor_property("visible")
                hidden = obj.get_editor_property("hidden_in_game")
                print(f"  Loc={loc}, Rot={rot}, Scale={scale}, Vis={vis}, HiddenInGame={hidden}", flush=True)
            if isinstance(obj, unreal.PaperFlipbookComponent):
                fb = obj.get_editor_property("source_flipbook")
                print(f"  SourceFlipbook: {fb.get_path_name() if fb else 'None'}", flush=True)
                trans = obj.get_editor_property("translucency_sort_priority")
                print(f"  TranslucencySortPriority: {trans}", flush=True)
            if isinstance(obj, unreal.PrimitiveComponent):
                try:
                    bi = obj.get_editor_property("body_instance")
                    print(f"  CollisionProfile: {bi.get_editor_property('collision_profile_name')}, Enabled: {bi.get_editor_property('collision_enabled')}, SimulatePhysics: {bi.get_editor_property('simulate_physics')}", flush=True)
                except Exception as e:
                    print(f"  Collision error: {e}", flush=True)

    print("\n=== DUMPING MAP ACTORS ===")
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if world:
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
        for a in actors:
            lbl = a.get_actor_label()
            cls = a.get_class().get_name()
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            scale = a.get_actor_scale3d()
            if "Camera" in lbl or "Camera" in cls or "Player" in lbl or "Start" in lbl:
                print(f"Actor: {lbl} ({cls}) -> Loc={loc}, Rot={rot}, Scale={scale}")
                if isinstance(a, unreal.CameraActor):
                    cam_comp = a.get_component_by_class(unreal.CameraComponent)
                    if cam_comp:
                        proj = cam_comp.get_editor_property("projection_mode")
                        fov = cam_comp.get_editor_property("field_of_view")
                        ortho_w = cam_comp.get_editor_property("ortho_width")
                        near_clip = cam_comp.get_editor_property("ortho_near_clip_plane")
                        far_clip = cam_comp.get_editor_property("ortho_far_clip_plane")
                        print(f"  Camera ProjectionMode={proj}, FOV={fov}, OrthoWidth={ortho_w}, NearClip={near_clip}, FarClip={far_clip}", flush=True)
            elif "GameMode" in lbl or "GameMode" in cls:
                print(f"GameMode Actor: {lbl} ({cls})", flush=True)

    # 检查 WorldSettings 和 DefaultGameMode
    ws = world.get_world_settings()
    gm = ws.get_editor_property("default_game_mode")
    print(f"\nDefaultGameMode: {gm.get_path_name() if gm else 'None'}", flush=True)
    if gm:
        try:
            cdo_gm = unreal.get_default_object(gm)
            pawn_cls = cdo_gm.get_editor_property("default_pawn_class")
            print(f"  DefaultPawnClass: {pawn_cls.get_path_name() if pawn_cls else 'None'}", flush=True)
        except Exception as e:
            print(f"  DefaultPawnClass query error: {e}", flush=True)

if __name__ == "__main__":
    dump_all()
