# -*- coding: utf-8 -*-
import unreal

def inspect_blueprint(bp_path):
    print(f"\n==================== INSPECT BLUEPRINT: {bp_path} ====================")
    bp = unreal.load_asset(bp_path)
    if not bp:
        print(f"FAILED TO LOAD: {bp_path}")
        return
    
    gen_cls = bp.generated_class()
    cdo = unreal.get_default_object(gen_cls) if gen_cls else None
    print(f"ParentClass: {bp.get_editor_property('parent_class').get_name()}")
    
    # Subobjects
    handles = unreal.SubobjectDataBlueprintFunctionLibrary.k2_gather_subobject_data_for_blueprint(bp)
    print(f"Total Subobjects: {len(handles)}")
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        cls_name = obj.get_class().get_name() if obj else "None"
        print(f"  Subobject: '{vname}' (Class: {cls_name})")
        if obj and isinstance(obj, unreal.PrimitiveComponent):
            try:
                prof = obj.get_editor_property("collision_profile_name")
                enabled = obj.get_collision_enabled()
                gen_overlap = obj.get_editor_property("generate_overlap_events")
                # check response to Pawn
                pawn_resp = obj.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)
                print(f"    PrimitiveComp Collision: Profile='{prof}', Enabled={enabled}, GenOverlap={gen_overlap}, ResponseToPawn={pawn_resp}")
            except Exception as e:
                print(f"    PrimitiveComp check error: {e}")
                
    # Check CDO components
    if cdo:
        all_comps = cdo.get_components_by_class(unreal.ActorComponent)
        print(f"  CDO Components: {len(all_comps)}")
        for c in all_comps:
            print(f"    CDO Comp: {c.get_name()} ({c.get_class().get_name()})")
            if isinstance(c, unreal.PrimitiveComponent):
                prof = c.get_editor_property("collision_profile_name")
                pawn_resp = c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)
                print(f"      CDO Coll: Profile='{prof}', PawnResp={pawn_resp}")

inspect_blueprint("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
inspect_blueprint("/Game/Blueprints/Player/BP_Player_Medic")
inspect_blueprint("/Game/Blueprints/Stage/BP_StageWaveManager")
inspect_blueprint("/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker")
inspect_blueprint("/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound")

print("\n==================== INSPECT COMPLETE ====================")
