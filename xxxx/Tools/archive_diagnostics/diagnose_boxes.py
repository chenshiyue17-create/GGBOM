# -*- coding: utf-8 -*-
import unreal

bps = [
    '/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord',
    '/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker',
    '/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound'
]
for p in bps:
    bp = unreal.EditorAssetLibrary.load_asset(p)
    if not bp:
        continue
    cdo = unreal.get_default_object(bp.generated_class())
    comps = cdo.get_components_by_class(unreal.BoxComponent)
    print(f"=== {p} ===")
    for c in comps:
        ext = c.get_editor_property("box_extent") if hasattr(c, "box_extent") else "N/A"
        col = c.get_collision_enabled()
        prof = c.get_collision_profile_name()
        print(f"  Box: {c.get_name()}, extent={ext}, col_enabled={col}, profile={prof}")
