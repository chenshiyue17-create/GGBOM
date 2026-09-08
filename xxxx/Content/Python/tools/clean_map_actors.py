# -*- coding: utf-8 -*-
"""
清理 MAP_GGBOM_Main 关卡中的伪 UI 精灵 Actor 和写死的静态木桩敌人。
只保留：
- PlayerStart
- PortraitCamera_9x16
- Ground_Stage00
- 阻挡墙体 (Wall_*)
- 掩体路障 (Barricade_*, DefenseLine_*)
"""
from __future__ import annotations
import unreal

world_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
world = unreal.EditorLoadingAndSavingUtils.load_map(world_path)
if not world:
    raise RuntimeError(f"无法加载关卡: {world_path}")

actors = unreal.EditorLevelLibrary.get_all_level_actors()
removed = []
kept = []

for a in actors:
    lbl = a.get_actor_label()
    cls_name = a.get_class().get_name()
    
    # 判定是否需要删除
    # 1. 假 UI 精灵 (UI_BossBar_*, UI_Player_*, UI_HUD_*, UI_Btn_*)
    # 2. 关卡写死的敌人木桩 (Enemy_*, Boss_*)
    should_delete = False
    if lbl.startswith("UI_"):
        should_delete = True
    elif lbl.startswith("Enemy_") or lbl.startswith("Boss_"):
        should_delete = True
        
    if should_delete:
        removed.append(f"{lbl} ({cls_name})")
        unreal.EditorLevelLibrary.destroy_actor(a)
    else:
        kept.append(f"{lbl} ({cls_name})")

unreal.EditorLoadingAndSavingUtils.save_map(world, world_path)

print(f"=== 关卡清理完成 ===")
print(f"已删除 Actor 数量: {len(removed)}")
for r in removed:
    print(f"  - 移除: {r}")
print(f"保留 Actor 数量: {len(kept)}")
for k in kept:
    print(f"  + 保留: {k}")

with open("/Users/cc/Desktop/GGBOM/xxxx/output/cleaned_map_actors.txt", "w", encoding="utf-8") as f:
    f.write("Removed:\n" + "\n".join(removed) + "\n\nKept:\n" + "\n".join(kept))
