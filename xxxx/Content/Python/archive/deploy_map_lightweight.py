# -*- coding: utf-8 -*-
import unreal

MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
WAVEMGR_PATH = "/Game/Blueprints/Stage/BP_StageWaveManager"

print(f"[Deploy] 正在加载地图: {MAP_PATH}...")
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    print(f"❌ 无法加载地图: {MAP_PATH}")
    unreal.SystemLibrary.quit_editor()

actors = unreal.EditorLevelLibrary.get_all_level_actors()
has_wave_mgr = False
for a in actors:
    cls_name = a.get_class().get_name()
    if "BP_StageWaveManager" in cls_name:
        has_wave_mgr = True
        print(f"  - 关卡已有波次调度实体: {a.get_actor_label()}")
        break

if not has_wave_mgr:
    wave_bp = unreal.load_asset(WAVEMGR_PATH)
    if wave_bp:
        gen_cls = wave_bp.generated_class()
        spawned = unreal.EditorLevelLibrary.spawn_actor_from_class(gen_cls, unreal.Vector(0, 0, 600))
        if spawned:
            spawned.set_actor_label("BP_StageWaveManager_Live")
            print("  ✅ 已成功在关卡部署 BP_StageWaveManager_Live 调度实体！")

unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
print("🎉 MAP_GGBOM_Main 关卡已就绪并成功保存！")
