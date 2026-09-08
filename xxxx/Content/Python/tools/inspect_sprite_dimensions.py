# -*- coding: utf-8 -*-
import unreal

def inspect_dimensions():
    out = []
    
    # 检查主角 Flipbook
    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    fb_idle_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    if fb_idle_up:
        s0 = fb_idle_up.get_sprite_at_frame(0)
        if s0:
            sz = s0.get_source_size()
            pivot = s0.get_pivot_position()
            out.append(f"Player Sprite Size: {sz}, Pivot: {pivot}")
            
    # 检查子弹 Flipbook
    bullet_fb = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/03_Weapons/01_KineticPistol/Flipbooks/FB_T_Bullet_KineticPistol_Sheet")
    if bullet_fb:
        bs0 = bullet_fb.get_sprite_at_frame(0)
        if bs0:
            bsz = bs0.get_source_size()
            bpivot = bs0.get_pivot_position()
            out.append(f"Bullet Sprite Size: {bsz}, Pivot: {bpivot}")

    with open("/Users/cc/Desktop/GGBOM/sprite_dimensions.txt", "w") as f:
        f.write("\n".join(out))
    print("DONE_INSPECT_DIMENSIONS")

if __name__ == "__main__":
    inspect_dimensions()
