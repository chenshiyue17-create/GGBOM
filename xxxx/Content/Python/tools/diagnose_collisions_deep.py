# -*- coding: utf-8 -*-
import unreal
import json

def inspect_bp(bp_path):
    bp = unreal.load_asset(bp_path)
    if not bp:
        return {"error": "not found"}
    
    cdo = unreal.get_default_object(bp.generated_class())
    components = []
    root_comp_name = "None"
    if cdo:
        root = cdo.get_editor_property("root_component") if hasattr(cdo, "root_component") else None
        if root:
            root_comp_name = f"{root.get_name()} ({root.get_class().get_name()})"
            
        for c in cdo.get_components_by_class(unreal.ActorComponent):
            c_info = {
                "name": c.get_name(),
                "class": c.get_class().get_name(),
            }
            if isinstance(c, unreal.PrimitiveComponent):
                try:
                    c_info["collision_enabled"] = str(c.get_collision_enabled())
                    c_info["collision_profile"] = str(c.get_collision_profile_name())
                    if hasattr(c, "get_generate_overlap_events"):
                        c_info["generate_overlap_events"] = c.get_generate_overlap_events()
                    elif c.has_editor_property("generate_overlap_events"):
                        c_info["generate_overlap_events"] = c.get_editor_property("generate_overlap_events")
                except Exception:
                    pass

                if isinstance(c, unreal.BoxComponent):
                    ext = c.get_editor_property("box_extent")
                    c_info["box_extent"] = [ext.x, ext.y, ext.z]
                elif isinstance(c, unreal.CapsuleComponent):
                    c_info["capsule_radius"] = c.get_editor_property("capsule_radius")
                    c_info["capsule_half_height"] = c.get_editor_property("capsule_half_height")
            components.append(c_info)
            
    parent_name = "None"
    try:
        if hasattr(bp, "parent_class") and bp.parent_class:
            parent_name = bp.parent_class.get_name()
    except Exception:
        pass

    return {
        "path": bp_path,
        "parent": parent_name,
        "root_component": root_comp_name,
        "components": components
    }

def main():
    report = {}
    bps_to_check = [
        "/Game/Blueprints/Player/BP_Player_Medic",
        "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
        "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord",
        "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
    ]
    for p in bps_to_check:
        report[p] = inspect_bp(p)
        
    world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/GGBOM/Maps/MAP_GGBOM_Main")
    level_actors = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        loc = a.get_actor_location()
        cls_name = a.get_class().get_name()
        colls = []
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            colls.append({
                "comp": c.get_name(),
                "class": c.get_class().get_name(),
                "col_enabled": str(c.get_collision_enabled()),
                "profile": str(c.get_collision_profile_name())
            })
        level_actors.append({
            "label": lbl,
            "class": cls_name,
            "loc": [loc.x, loc.y, loc.z],
            "primitives": colls
        })
    report["level_actors"] = level_actors
    
    out_path = "/Users/cc/Desktop/GGBOM/xxxx/output/collision_audit_deep.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("COLLISION_AUDIT_DEEP_COMPLETE")

if __name__ == "__main__":
    main()
