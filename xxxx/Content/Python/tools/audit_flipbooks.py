# -*- coding: utf-8 -*-
import unreal

fb_paths = [
    "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet",
    "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet",
    "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet",
    "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet",
    "/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet",
    "/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet",
    "/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet",
    "/Game/P01/Imported/Content/Asset/Art/01_Player/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet"
]

lines = []
for p in fb_paths:
    fb = unreal.load_asset(p)
    if not fb:
        lines.append(f"FAILED TO LOAD: {p}")
        continue
    fps = fb.get_editor_property("frames_per_second")
    num_f = fb.get_num_frames()
    num_kf = fb.get_num_key_frames()
    lines.append(f"Flipbook: {fb.get_name()} | FPS: {fps} | TotalFrames: {num_f} | KeyFrames: {num_kf}")
    for k in range(num_kf):
        sprite = fb.get_sprite_at_frame(k)
        lines.append(f"  KF[{k}]: sprite={sprite.get_name() if sprite else 'None'}")

with open("/Users/cc/Desktop/GGBOM/xxxx/flipbook_audit.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("AUDIT_FILE_WRITTEN")
