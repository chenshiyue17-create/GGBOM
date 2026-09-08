# -*- coding: utf-8 -*-
import unreal
import json

def inspect_asset_nodes(bp):
    uber_graph_pages = bp.get_editor_property("uber_graph_pages")
    all_nodes = []
    for page in uber_graph_pages:
        nodes = page.get_editor_property("nodes")
        for node in nodes:
            n_class = node.get_class().get_name()
            n_title = node.get_node_title(unreal.NodeTitleType.FULL_TITLE)
            all_nodes.append({
                "page": page.get_name(),
                "node_class": n_class,
                "node_title": str(n_title)
            })
    return all_nodes

def inspect_collision(obj):
    info = {}
    if hasattr(obj, "get_collision_enabled"):
        info["collision_enabled"] = str(obj.get_collision_enabled())
    if hasattr(obj, "get_collision_profile_name"):
        info["profile_name"] = str(obj.get_collision_profile_name())
    if hasattr(obj, "get_collision_object_type"):
        info["object_type"] = str(obj.get_collision_object_type())
    if hasattr(obj, "get_generate_overlap_events"):
        info["generate_overlap_events"] = obj.get_generate_overlap_events()
    
    # channels
    channels = {
        "WorldStatic": unreal.CollisionChannel.ECC_WORLD_STATIC,
        "WorldDynamic": unreal.CollisionChannel.ECC_WORLD_DYNAMIC,
        "Pawn": unreal.CollisionChannel.ECC_PAWN,
        "PhysicsBody": unreal.CollisionChannel.ECC_PHYSICS_BODY,
        "Vehicle": unreal.CollisionChannel.ECC_VEHICLE,
        "Destructible": unreal.CollisionChannel.ECC_DESTRUCTIBLE
    }
    responses = {}
    for c_name, c_val in channels.items():
        if hasattr(obj, "get_collision_response_to_channel"):
            responses[c_name] = str(obj.get_collision_response_to_channel(c_val))
    info["responses"] = responses
    return info

def run_inspect():
    out = {}
    
    # 1. Inspect BP_ProjectileBase
    bp_proj = unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
    if bp_proj:
        out["projectile_nodes"] = inspect_asset_nodes(bp_proj)
        
        # inspect components
        subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        handles = subsys.k2_gather_subobject_data_for_blueprint(bp_proj)
        comp_info = {}
        for h in handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp_proj)
            if obj and isinstance(obj, unreal.PrimitiveComponent):
                comp_info[vname] = {
                    "class": obj.get_class().get_name(),
                    "collision": inspect_collision(obj)
                }
        out["projectile_components"] = comp_info
    
    # 2. Inspect Enemy Blueprints
    enemy_bps = [
        "/Game/Blueprints/Enemies/BP_Enemy_Zombie",
        "/Game/Blueprints/Enemies/BP_Enemy_MutantHound",
        "/Game/Blueprints/Enemies/BP_Boss_Overlord"
    ]
    enemy_info = {}
    for ep in enemy_bps:
        ebp = unreal.EditorAssetLibrary.load_asset(ep)
        if ebp:
            e_comps = {}
            subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
            handles = subsys.k2_gather_subobject_data_for_blueprint(ebp)
            for h in handles:
                data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
                vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
                obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, ebp)
                if obj and isinstance(obj, unreal.PrimitiveComponent):
                    e_comps[vname] = {
                        "class": obj.get_class().get_name(),
                        "collision": inspect_collision(obj)
                    }
            enemy_info[ep] = {
                "components": e_comps,
                "nodes": inspect_asset_nodes(ebp)
            }
        else:
            enemy_info[ep] = "NOT_FOUND"
    out["enemies"] = enemy_info

    # 3. Write to output
    out_file = "/Users/cc/Desktop/GGBOM/xxxx/output/bullet_enemy_diagnostic.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    unreal.log(f"[DIAGNOSTIC] Exported diagnostic to {out_file}")
    print(f"[DIAGNOSTIC] Exported diagnostic to {out_file}")

if __name__ == "__main__" or True:
    run_inspect()
