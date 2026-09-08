# -*- coding: utf-8 -*-
import unreal

def check_asset(p):
    fb = unreal.load_asset(p)
    if fb:
        sp = fb.get_sprite_at_frame(0)
        print(f"PATH: {p}")
        print(f"  Sprite: {sp.get_name() if sp else 'None'}")
    else:
        print(f"NOT FOUND: {p}")

pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
check_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet")
check_asset(f"{pfx}/02_Attack_Hurt/Dir_03_Right/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_03_Right_Sheet")
