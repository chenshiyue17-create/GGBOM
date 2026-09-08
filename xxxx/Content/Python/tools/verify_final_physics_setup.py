# -*- coding: utf-8 -*-
import json
import unreal

report = {
    "enemies_upgraded": [],
    "player_upgraded": False,
    "barricade_walls": [],
    "boundary_walls": [],
    "enemies_aligned": []
}

# 1. 验证敌人蓝图
subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
enemy_names = [
    "BP_Enemy_ZombieWalker", "BP_Enemy_ZombieRunner", "BP_Enemy_MutantHound",
    "BP_Enemy_VenomShooter", "BP_Enemy_ArmoredGuard", "BP_Enemy_MutantBrute",
    "BP_Boss_Overlord"
]

for name in enemy_names:
    bp = unreal.load_asset(f"/Game/Blueprints/Characters/Enemies/{name}")
    if not bp:
        continue
    handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)
    has_box = False
    has_pmc = False
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if isinstance(obj, unreal.BoxComponent):
            has_box = True
        elif isinstance(obj, unreal.ProjectileMovementComponent):
            has_pmc = True
    report["enemies_upgraded"].append({
        "name": name,
        "has_box_collision": has_box,
        "has_projectile_movement": has_pmc
    })

# 2. 验证玩家蓝图
player_bp = unreal.load_asset("/Game/Blueprints/Player/BP_Player_Medic")
if player_bp:
    handles = subsystems.k2_gather_subobject_data_for_blueprint(player_bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, player_bp)
        if isinstance(obj, unreal.BoxComponent):
            report["player_upgraded"] = True
            break

# 3. 验证地图
world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/GGBOM/Maps/MAP_GGBOM_Main")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in actors:
    lbl = a.get_actor_label()
    loc = a.get_actor_location()
    if lbl.startswith("Wall_Barricade") or lbl.startswith("Wall_Defense"):
        report["barricade_walls"].append({"label": lbl, "location": [loc.x, loc.y, loc.z]})
    elif lbl.startswith("Wall_Boundary"):
        report["boundary_walls"].append({"label": lbl, "location": [loc.x, loc.y, loc.z]})
    elif lbl.startswith("Enemy_") or lbl.startswith("Boss_"):
        report["enemies_aligned"].append({"label": lbl, "location": [loc.x, loc.y, loc.z]})

out_path = "/Users/cc/Desktop/GGBOM/xxxx/output/final_physics_verification.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

unreal.log(f"Verification report written to {out_path}")
print(json.dumps(report, indent=2))
