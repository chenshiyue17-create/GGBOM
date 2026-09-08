# -*- coding: utf-8 -*-
import unreal

p1 = "/Game/P01/Imported/Content/Asset/Art/03_Weapons/01_KineticPistol/Flipbooks/FB_T_Bullet_KineticPistol_Sheet"
p2 = "/Game/P01/Representative/Intermediate/P01/Generated/ProjectileFlight4/01_KineticPistol/Flipbooks/FB_T_Bullet_KineticPistol_02_Flight_Strict4"

a1 = unreal.load_asset(p1)
a2 = unreal.load_asset(p2)

out = []
out.append(f"p1: {a1 is not None}")
out.append(f"p2: {a2 is not None}")

# 搜索所有包含 Bullet 的 Flipbook
assets = unreal.EditorAssetLibrary.list_assets("/Game", recursive=True, include_folder=False)
bullet_assets = [a for a in assets if "bullet" in a.lower() and "flipbook" in a.lower()]
out.append(f"Bullet Flipbooks: {bullet_assets}")

with open("/Users/cc/Desktop/GGBOM/bullet_assets.txt", "w") as f:
    f.write("\n".join(out))
print("DONE_BULLET_CHECK")
