# -*- coding: utf-8 -*-
import unreal

bps = [
    "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase",
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound",
    "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord",
    "/Game/Blueprints/Pickups/BP_Pickup_ExpGem",
    "/Game/Blueprints/Stage/BP_StageWaveManager"
]

with open("/Users/cc/Desktop/GGBOM/xxxx/output/bp_parents.txt", "w", encoding="utf-8") as f:
    for p in bps:
        bp = unreal.load_asset(p)
        parent_class = unreal.BlueprintEditorLibrary.get_blueprint_parent_class(bp)
        f.write(f"BP: {p} | Parent: {parent_class.get_name()}\n")

print("Done bp_parents.py")
