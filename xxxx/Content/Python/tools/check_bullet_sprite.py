# -*- coding: utf-8 -*-
import unreal

fb_path = "/Game/P01/Imported/Content/Asset/Art/03_Weapons/01_KineticPistol/Flipbooks/FB_T_Bullet_KineticPistol_Sheet"
fb = unreal.load_asset(fb_path)

out = []
if fb:
    out.append(f"Flipbook: {fb.get_name()}, Frames: {fb.get_num_frames()}")
    sprite = fb.get_sprite_at_frame(0)
    if sprite:
        out.append(f"Sprite: {sprite.get_name()}")
        mat = sprite.get_default_material()
        out.append(f"Material: {mat.get_name() if mat else 'None'}")
        if mat:
            out.append(f"TwoSided: {mat.get_editor_property('two_sided') if hasattr(mat, 'two_sided') else 'N/A'}")

with open("/Users/cc/Desktop/GGBOM/bullet_sprite_info.txt", "w") as f:
    f.write("\n".join(out))
print("DONE_SPRITE_INFO")
