# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》待机动画播放速率放慢 0.5 倍 (50% Speed)
- 将所有玩家待机 Flipbook 资产的 frames_per_second 减半
- 持久化保存所有受影响的 Flipbook 资产
================================================================================
"""
from __future__ import annotations
import unreal

ASSETS = unreal.EditorAssetLibrary

pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run"
idle_flipbook_paths = [
    f"{pfx}/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet",
    f"{pfx}/Dir_02_DownLeft/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_02_DownLeft_Sheet",
    f"{pfx}/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet",
    f"{pfx}/Dir_04_UpLeft/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_04_UpLeft_Sheet",
    f"{pfx}/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet",
]

def main():
    print("================================================================")
    print("⏳ 开始调整待机动画速率 (降低 0.5 倍)...")
    print("================================================================")
    
    modified_count = 0
    for path in idle_flipbook_paths:
        if not ASSETS.does_asset_exist(path):
            print(f"⚠️ 未找到 Flipbook: {path}")
            continue
            
        fb = unreal.load_asset(path)
        if not fb:
            continue
            
        old_fps = float(fb.get_editor_property("frames_per_second"))
        new_fps = max(1.0, old_fps * 0.5)
        fb.set_editor_property("frames_per_second", new_fps)
        ASSETS.save_loaded_asset(fb, only_if_is_dirty=False)
        print(f"✅ {fb.get_name()}: FPS {old_fps:.1f} -> {new_fps:.1f} (放慢 0.5 倍)")
        modified_count += 1
        
    print(f"🎉 成功调整 {modified_count} 个待机 Flipbook 动画帧率！")

if __name__ == "__main__":
    main()
