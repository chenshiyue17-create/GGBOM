# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from pathlib import Path
import unreal

BPLIB = unreal.BlueprintEditorLibrary
ASSETS = unreal.EditorAssetLibrary

out_data = {}

def inspect_bp(bp_path: str):
    bp = unreal.load_asset(bp_path)
    if not bp:
        return {"exists": False}
    
    parent_name = "Unknown"
    try:
        gen_class = bp.generated_class()
        if gen_class:
            super_cls = gen_class.get_super_class()
            if super_cls:
                parent_name = super_cls.get_name()
    except Exception as e:
        parent_name = str(e)

    info = {
        "exists": True,
        "parent_class": parent_name,
        "variables": [],
        "graphs": [],
        "components": []
    }
    
    try:
        info["variables"] = [str(v) for v in BPLIB.list_member_variable_names(bp, False)]
    except Exception as e:
        info["variables_err"] = str(e)
        
    try:
        info["graphs"] = [str(g) for g in BPLIB.list_graph_names(bp)]
    except Exception as e:
        info["graphs_err"] = str(e)

    # 检查 CDO
    try:
        cdo = unreal.get_default_object(bp.generated_class())
        if cdo:
            comps = cdo.get_components_by_class(unreal.ActorComponent)
            for c in comps:
                c_info = {
                    "name": c.get_name(),
                    "class": c.get_class().get_name()
                }
                if isinstance(c, unreal.PrimitiveComponent):
                    try:
                        c_info["collision_enabled"] = str(c.get_collision_enabled())
                        c_info["collision_profile"] = str(c.get_collision_profile_name())
                        c_info["generate_overlap_events"] = bool(c.get_editor_property("generate_overlap_events"))
                    except Exception:
                        pass
                info["components"].append(c_info)
    except Exception as e:
        info["cdo_err"] = str(e)
        
    return info

blueprints_to_check = {
    "Player": "/Game/Blueprints/Player/BP_Player_Medic",
    "Projectile": "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase",
    "Zombie": "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
    "Hound": "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound",
    "Boss": "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord",
    "WaveManager": "/Game/Blueprints/Stage/BP_StageWaveManager",
    "ExpGem": "/Game/Blueprints/Pickups/BP_Pickup_ExpGem",
    "CombatHUD": "/Game/GGBOM/UI/WBP_GGBOM_CombatHUD",
    "BossBar": "/Game/GGBOM/UI/WBP_Boss_OverheadHealthBar"
}

for k, p in blueprints_to_check.items():
    try:
        out_data[k] = inspect_bp(p)
    except Exception as e:
        out_data[k] = {"error": str(e)}

# 检查关卡 MAP_GGBOM_Main
try:
    world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/GGBOM/Maps/MAP_GGBOM_Main")
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    actor_list = []
    for a in actors:
        actor_list.append({
            "label": a.get_actor_label(),
            "class": a.get_class().get_name(),
            "location": [round(a.get_actor_location().x, 1), round(a.get_actor_location().y, 1), round(a.get_actor_location().z, 1)]
        })
    out_data["map_actors"] = actor_list
except Exception as e:
    out_data["map_actors_err"] = str(e)

out_file = "/Users/cc/Desktop/GGBOM/xxxx/output/deep_game_flow_audit.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(out_data, f, ensure_ascii=False, indent=2)

print(f"Deep audit written to {out_file}")
unreal.log(f"Deep audit written to {out_file}")
