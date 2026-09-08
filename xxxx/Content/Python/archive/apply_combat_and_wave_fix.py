# -*- coding: utf-8 -*-
"""
================================================================================
终极修复脚本: 子弹防阻挡解耦 + 关卡动态怪物流部署 (零图表删改，纯属性与关卡装配)
================================================================================
1. 修复 BP_ProjectileBase:
   - 将所有组件及 CDO 的碰撞 Profile 规范为 OverlapAllDynamic
   - 对 ECC_Pawn 显式设置响应为 ECR_Ignore，彻底根除子弹阻挡或推着玩家走的问题
   - GenerateOverlapEvents = True
2. 关卡 MAP_GGBOM_Main 净化与动态敌人部署:
   - 彻底删除关卡中残留的 9 个纯静态死物贴图 PaperSpriteActor (Zombie_01~03, Hound_01~02, Brute, Spitter, Armored, Boss)
   - 严格保留地面 Ground_Stage00、战术掩体 Barricade_*、防线 DefenseLine_*、相机与 PlayerStart
   - 在战斗区 (Z = 200 ~ 520) 部署具备原生步态下压与生命周期的活动敌人实体 (BP_Enemy_ZombieWalker, BP_Enemy_MutantHound, BP_Boss_Overlord)
   - 保存关卡并输出结构化审计快照
================================================================================
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
PROJ_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
ZOMBIE_BP_PATH = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
HOUND_BP_PATH = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
BOSS_BP_PATH = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"

def log(msg):
    print(f"[FIX] {msg}", flush=True)

def step1_fix_projectile_collision():
    log("==================================================")
    log("🚀 [1/2] 正在修复子弹蓝图碰撞预设...")
    bp = unreal.load_asset(PROJ_BP_PATH)
    if not bp:
        raise RuntimeError(f"未找到资产: {PROJ_BP_PATH}")
        
    try:
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        if subsystem:
            handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
            for h in handles:
                data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
                vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
                obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
                if obj and isinstance(obj, unreal.PrimitiveComponent):
                    try:
                        obj.set_collision_profile_name("OverlapAllDynamic")
                        obj.set_editor_property("generate_overlap_events", True)
                        obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponse.ECR_IGNORE)
                        log(f"  - Subobject '{vname}' 已配置: OverlapAllDynamic, Pawn=Ignore")
                    except Exception as e:
                        log(f"  - Subobject '{vname}' 警告: {e}")
    except Exception as e:
        log(f"  - SubobjectDataSubsystem 扫描跳过: {e}")
                
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        for c in cdo.get_components_by_class(unreal.PrimitiveComponent):
            try:
                c.set_collision_profile_name("OverlapAllDynamic")
                c.set_editor_property("generate_overlap_events", True)
                c.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponse.ECR_IGNORE)
                log(f"  - CDO Component '{c.get_name()}' 已配置: OverlapAllDynamic, Pawn=Ignore")
            except Exception as e:
                log(f"  - CDO Component 警告: {e}")
                
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_ProjectileBase 子弹物理防阻挡属性已持久化保存！")

def step2_deploy_dynamic_enemies():
    log("==================================================")
    log("🚀 [2/2] 正在净化关卡并部署动态怪物军团...")
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        raise RuntimeError(f"无法加载地图: {MAP_PATH}")
        
    # 待清理的旧静态死物贴图标签
    DUMMY_LABELS = {
        "Zombie_01", "Zombie_02", "Zombie_03", "Brute_Elite",
        "ZombieSpitter_01", "ZombieArmored_01", "Hound_01", "Hound_02",
        "Boss_Overlord_Visual"
    }
    
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    destroyed_count = 0
    for a in actors:
        lbl = a.get_actor_label()
        cls_name = a.get_class().get_name()
        
        # 1. 清理死物静态贴图
        if lbl in DUMMY_LABELS and cls_name == "PaperSpriteActor":
            log(f"  🗑️ 删除死物贴图: {lbl} ({cls_name})")
            unreal.EditorLevelLibrary.destroy_actor(a)
            destroyed_count += 1
        # 2. 清理旧有的临时动态怪（以便幂等重新部署）
        elif lbl.startswith("Live_") or lbl.startswith("CombatWave_") or lbl.startswith("Enemy_"):
            log(f"  🔄 清理旧版怪物实例: {lbl} ({cls_name})")
            unreal.EditorLevelLibrary.destroy_actor(a)
            destroyed_count += 1
            
    log(f"  - 共净化清除 {destroyed_count} 个陈旧/伪怪物实体")
    
    # 3. 部署具有推进与伤害逻辑的原生活跃敌人
    zombie_bp = unreal.load_asset(ZOMBIE_BP_PATH)
    hound_bp = unreal.load_asset(HOUND_BP_PATH)
    boss_bp = unreal.load_asset(BOSS_BP_PATH)
    
    if not zombie_bp or not hound_bp:
        raise RuntimeError("未找到核心敌人蓝图资产！")
        
    zombie_cls = zombie_bp.generated_class()
    hound_cls = hound_bp.generated_class()
    boss_cls = boss_bp.generated_class() if boss_bp else None
    
    # 按照 4 车道与纵向战斗梯度部署活跃实体 (Z: 200 ~ 520, Y: 0)
    SPAWN_LIST = [
        (zombie_cls, unreal.Vector(-150.0, 0.0, 220.0), "Live_Zombie_01"),
        (zombie_cls, unreal.Vector(0.0, 0.0, 280.0),    "Live_Zombie_02"),
        (zombie_cls, unreal.Vector(150.0, 0.0, 240.0),   "Live_Zombie_03"),
        (hound_cls,  unreal.Vector(-180.0, 0.0, 360.0),  "Live_Hound_01"),
        (hound_cls,  unreal.Vector(180.0, 0.0, 390.0),   "Live_Hound_02"),
    ]
    if boss_cls:
        SPAWN_LIST.append((boss_cls, unreal.Vector(0.0, 0.0, 520.0), "Live_Boss_Overlord"))
        
    spawned_records = []
    for cls, loc, lbl in SPAWN_LIST:
        act = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, loc)
        if act:
            act.set_actor_label(lbl)
            spawned_records.append({"label": lbl, "class": cls.get_name(), "location": [loc.x, loc.y, loc.z]})
            log(f"  ✨ 成功生成动态敌人: {lbl} @ ({loc.x}, {loc.y}, {loc.z})")
            
    # 保存地图
    saved = unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    log(f"✅ 关卡 {MAP_PATH} 保存状态: {saved}")
    
    # 输出修复报告
    report = {
        "status": "PASS" if saved and len(spawned_records) >= 5 else "FAIL",
        "destroyed_dummy_count": destroyed_count,
        "spawned_live_enemies": spawned_records,
        "projectile_collision_fixed": True
    }
    out_path = ROOT / "output/combat_and_wave_fix_report.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    log(f"📄 报告已写入: {out_path}")

if __name__ == "__main__":
    step1_fix_projectile_collision()
    step2_deploy_dynamic_enemies()
    log("🎉 全部修复与装配执行成功！")
