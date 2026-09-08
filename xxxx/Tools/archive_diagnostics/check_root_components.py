# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ASSETS = unreal.EditorAssetLibrary

bps = [
    "/Game/Blueprints/Player/BP_Player_Medic",
    "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord",
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
]

lines = []
for p in bps:
    bp = ASSETS.load_asset(p)
    if not bp:
        continue
    cdo = unreal.get_default_object(bp.generated_class())
    root = cdo.get_editor_property("root_component") if hasattr(cdo, "root_component") else None
    if not root and hasattr(cdo, "get_root_component"):
        root = cdo.get_root_component()
    lines.append(f"BP: {p}")
    lines.append(f"  RootComponent: {root.get_name() if root else 'None'} ({root.get_class().get_name() if root else 'None'})")
    if root:
        lines.append(f"  Root Is Primitive: {isinstance(root, unreal.PrimitiveComponent)}")

print("\n".join(lines))
ROOT = Path(unreal.Paths.project_dir()).resolve()
(ROOT / "output/root_components.txt").write_text("\n".join(lines), encoding="utf-8")
