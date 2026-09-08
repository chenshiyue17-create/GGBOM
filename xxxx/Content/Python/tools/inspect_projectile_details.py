# -*- coding: utf-8 -*-
import unreal

proj_bp = unreal.load_asset("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
enemy_bp = unreal.load_asset("/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker")

def inspect_bp_components(bp, out_file):
    gen_class = bp.generated_class()
    cdo = unreal.get_default_object(gen_class)
    out_file.write(f"\n========================================\nBP: {bp.get_path_name()}\nCDO: {cdo.get_name()}\n")
    
    # 查找所有 Subobject / Components
    # 在 UE Python 中可以获取 Actor 的组件
    comps = cdo.get_components_by_class(unreal.ActorComponent)
    out_file.write(f"Components count on CDO: {len(comps)}\n")
    for c in comps:
        out_file.write(f"  Comp: {c.get_name()} | Class: {c.get_class().get_name()}\n")
        if isinstance(c, unreal.PrimitiveComponent):
            out_file.write(f"    CollisionEnabled: {c.get_editor_property('collision_enabled')}\n")
            out_file.write(f"    CollisionProfileName: {c.get_editor_property('collision_profile_name')}\n")
            out_file.write(f"    GenerateOverlapEvents: {c.get_editor_property('generate_overlap_events')}\n")

with open("/Users/cc/Desktop/GGBOM/xxxx/output/collision_details.txt", "w", encoding="utf-8") as f:
    inspect_bp_components(proj_bp, f)
    inspect_bp_components(enemy_bp, f)

print("Done inspect_projectile_details.py")
