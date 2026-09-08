# -*- coding: utf-8 -*-
import unreal

def check_fb(p):
    fb = unreal.load_asset(p)
    if fb:
        sp = fb.get_sprite_at_frame(0)
        print(f"FB: {p} -> Sprite: {sp.get_name() if sp else 'None'}")
    else:
        print(f"FB NOT FOUND: {p}")

check_fb("/Game/P01/Imported/Content/Asset/Art/01_Player/02_Attack_Hurt/Dir_03_Right/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_03_Right_Sheet")
check_fb("/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet")
check_fb("/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet")
