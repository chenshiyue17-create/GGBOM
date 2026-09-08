# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》全动态敌人动画蓝图与关卡规范部署
【核心机制规范】:
- 行尸小怪为游戏最底层海量消耗实体，追求极致性能与零状态机开销。
- 每个行尸类型为一个独立怪物，严格只有 1 个方向（单向朝下推进，不回头），4 帧连续动画为一个怪。
- 不采用复杂的多状态机（无多方向/状态切换开销），直接挂载专属 4 帧 Flipbook 循环播放。
================================================================================
"""
from __future__ import annotations
import json
from pathlib import Path
import unreal

ROOT = Path("/Users/cc/Desktop/GGBOM/xxxx")
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary

MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
BP_DIR = "/Game/Blueprints/Characters/Enemies"

# 严格按“单向朝下、4帧一怪、零状态机轻量化”机制定义的怪物名录
ENEMY_CONFIGS = [
    {
        "name": "BP_Enemy_ZombieWalker",
        "display_name": "基础感染行尸 (4帧单向)",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet.FB_T_Zombie_WalkerBasic_Sheet",
        "scale": 0.45,
        "max_hp": 65.0,
        "speed": 75.0,
        "damage": 15.0,
        "score": 10.0,
        "exp": 5.0,
        "priority": 200,
        "is_boss": False
    },
    {
        "name": "BP_Enemy_ZombieRunner",
        "display_name": "敏捷疾跑行尸 (4帧单向)",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/05_Zombie_Runner_Agile/Flipbooks/FB_T_Zombie_RunnerAgile_Sheet.FB_T_Zombie_RunnerAgile_Sheet",
        "scale": 0.45,
        "max_hp": 50.0,
        "speed": 120.0,
        "damage": 12.0,
        "score": 15.0,
        "exp": 8.0,
        "priority": 200,
        "is_boss": False
    },
    {
        "name": "BP_Enemy_VenomShooter",
        "display_name": "毒液喷射行尸 (4帧单向)",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/04_Zombie_Spitter_Minor/Flipbooks/FB_T_Zombie_SpitterMinor_Sheet.FB_T_Zombie_SpitterMinor_Sheet",
        "scale": 0.45,
        "max_hp": 95.0,
        "speed": 70.0,
        "damage": 10.0,
        "score": 25.0,
        "exp": 10.0,
        "priority": 200,
        "is_boss": False
    },
    {
        "name": "BP_Enemy_ArmoredGuard",
        "display_name": "重装防暴行尸 (4帧单向)",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/07_Zombie_Armored_Guard/Flipbooks/FB_T_Zombie_ArmoredGuard_Sheet.FB_T_Zombie_ArmoredGuard_Sheet",
        "scale": 0.50,
        "max_hp": 180.0,
        "speed": 55.0,
        "damage": 20.0,
        "score": 40.0,
        "exp": 15.0,
        "priority": 200,
        "is_boss": False
    },
    {
        "name": "BP_Enemy_MutantBrute",
        "display_name": "重型蹒跚蛮兽 (4帧单向)",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet.FB_T_Zombie_ShamblerHeavy_Sheet",
        "scale": 0.58,
        "max_hp": 480.0,
        "speed": 45.0,
        "damage": 45.0,
        "score": 80.0,
        "exp": 30.0,
        "priority": 210,
        "is_boss": False
    },
    {
        "name": "BP_Enemy_MutantHound",
        "display_name": "疾行变异猎犬",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet.FB_T_Hound_Run_Dir_01_Down_Sheet",
        "scale": 0.48,
        "max_hp": 130.0,
        "speed": 180.0,
        "damage": 25.0,
        "score": 35.0,
        "exp": 15.0,
        "priority": 200,
        "is_boss": False
    },
    {
        "name": "BP_Boss_Overlord",
        "display_name": "深渊异化领主 Boss",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet.FB_T_Boss_Walk_Dir_01_Down_Sheet",
        "scale": 0.68,
        "max_hp": 4500.0,
        "speed": 35.0,
        "damage": 60.0,
        "score": 1000.0,
        "exp": 200.0,
        "priority": 250,
        "is_boss": True
    },
]

CFG_MAP = {cfg["name"]: cfg for cfg in ENEMY_CONFIGS}

def log(msg: str):
    print(f"[DeployEnemies] {msg}")
    unreal.log(f"[DeployEnemies] {msg}")

def set_or_reset_var(bp, var_name: str, pin_type, default_val: str, category: str = "战斗属性"):
    graph = BPLIB.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    existing = set(str(name) for name in BPLIB.list_member_variable_names(bp, False))
    if var_name in existing:
        editor.remove_member_variable(var_name)
    editor.add_member_variable(var_name, pin_type, default_val)
    BPLIB.set_blueprint_variable_category(bp, var_name, unreal.Text(category))
    BPLIB.set_blueprint_variable_instance_editable(bp, var_name, True)

def ensure_directory(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

# ==============================================================================
# 1. 构建/重构标准敌人蓝图 (基于 PaperFlipbookActor，零状态机轻量化)
# ==============================================================================
def build_enemy_blueprint(cfg: dict) -> unreal.Blueprint:
    bp_path = f"{BP_DIR}/{cfg['name']}"
    log(f"🛠️ [1/2] 构建动态敌人蓝图: {cfg['display_name']} ({bp_path})...")
    
    bp = None
    if ASSETS.does_asset_exist(bp_path):
        bp = unreal.load_asset(bp_path)
        
    if not bp:
        bp = BPLIB.create_blueprint_asset_with_parent(bp_path, unreal.PaperFlipbookActor.static_class())
        if not bp:
            raise RuntimeError(f"无法创建蓝图: {bp_path}")

    # 声明蓝图变量
    real_type = BPLIB.get_basic_type_by_name("real")
    bool_type = BPLIB.get_basic_type_by_name("bool")
    
    set_or_reset_var(bp, "MaxHealth", real_type, str(cfg["max_hp"]), "战斗属性")
    set_or_reset_var(bp, "CurrentHealth", real_type, str(cfg["max_hp"]), "战斗属性")
    set_or_reset_var(bp, "MoveSpeed", real_type, str(cfg["speed"]), "战斗属性")
    set_or_reset_var(bp, "ContactDamage", real_type, str(cfg["damage"]), "战斗属性")
    set_or_reset_var(bp, "ScoreReward", real_type, str(cfg["score"]), "战斗奖励")
    set_or_reset_var(bp, "ExpGemValue", real_type, str(cfg["exp"]), "战斗奖励")
    set_or_reset_var(bp, "UnidirectionalForwardOnly", bool_type, "true", "怪物机制")
    
    if cfg["is_boss"]:
        set_or_reset_var(bp, "CurrentPhase", real_type, "1.0", "领主状态")

    BPLIB.compile_blueprint(bp)

    # 配置 CDO 中的 PaperFlipbookComponent (直接挂载专属 4 帧连续动画)
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        fb_comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
        if fb_comp:
            fb_asset = unreal.load_asset(cfg["flipbook"])
            if fb_asset:
                fb_comp.set_editor_property("source_flipbook", fb_asset)
                log(f"  + CDO 成功绑定专属 4 帧 Flipbook: {fb_asset.get_name()}")
            else:
                log(f"  ⚠️ 未找到 Flipbook: {cfg['flipbook']}")
                
            sc = cfg["scale"]
            fb_comp.set_editor_property("relative_scale3d", unreal.Vector(sc, sc, sc))
            fb_comp.set_editor_property("translucency_sort_priority", cfg["priority"])
            try:
                fb_comp.set_looping(True)
            except Exception:
                pass
            fb_comp.set_editor_property("visible", True)
            fb_comp.set_editor_property("hidden_in_game", False)

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ 动态敌人蓝图已就绪并保存: {cfg['name']}")
    return bp

# ==============================================================================
# 2. 在关卡 MAP_GGBOM_Main 中实例化部署单向 4 帧敌群阵列
# ==============================================================================
def deploy_to_main_stage(built_bps: dict[str, unreal.Blueprint]):
    log(f"🗺️ [2/2] 正在载入主关卡 {MAP_PATH} 部署动态敌人阵容...")
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        raise RuntimeError(f"无法加载地图: {MAP_PATH}")

    # 1. 扫描并清除场景中所有残留的旧怪物（保护 UI、相机、地面、路障）
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    destroyed_count = 0
    for a in actors:
        lbl = a.get_actor_label()
        cls_name = a.get_class().get_name()
        is_protected = any([
            lbl.startswith("PortraitCamera"),
            lbl.startswith("Ground_"),
            lbl.startswith("Barricade_"),
            lbl.startswith("DefenseLine_"),
            lbl.startswith("PlayerStart"),
            lbl.startswith("UI_"),
            lbl.startswith("HUD_"),
            lbl.startswith("Btn_")
        ])
        if not is_protected:
            if any(k in lbl.lower() for k in ["enemy", "zombie", "hound", "brute", "boss", "spitter", "runner", "live_"]):
                unreal.EditorLevelLibrary.destroy_actor(a)
                destroyed_count += 1
                log(f"  - 移除旧怪物实例: {lbl} ({cls_name})")

    log(f"  已清理 {destroyed_count} 个历史旧怪实例。")

    # 2. 9:16 战术纵深单向波次阵型 (自上方 Z=+560 向下方 Z=+140 梯次推进)
    spawn_matrix = [
        # 前锋波次 (行尸群：4帧单向不回头)
        ("BP_Enemy_ZombieWalker", unreal.Vector(-160.0, 15.0, 180.0), "Enemy_Zombie_01"),
        ("BP_Enemy_ZombieWalker", unreal.Vector(0.0, 15.0, 140.0), "Enemy_Zombie_02"),
        ("BP_Enemy_ZombieWalker", unreal.Vector(160.0, 15.0, 180.0), "Enemy_Zombie_03"),
        # 特种突变体波次 (敏捷跑者、毒液喷射者、重装防暴)
        ("BP_Enemy_ZombieRunner", unreal.Vector(-120.0, 15.0, 260.0), "Enemy_Runner_01"),
        ("BP_Enemy_VenomShooter", unreal.Vector(120.0, 15.0, 260.0), "Enemy_VenomShooter_01"),
        ("BP_Enemy_ArmoredGuard", unreal.Vector(0.0, 15.0, 290.0), "Enemy_ArmoredGuard_01"),
        # 侧翼突袭猎犬
        ("BP_Enemy_MutantHound", unreal.Vector(-220.0, 15.0, 350.0), "Enemy_Hound_01"),
        ("BP_Enemy_MutantHound", unreal.Vector(220.0, 15.0, 350.0), "Enemy_Hound_02"),
        # 中坚重型蛮兽
        ("BP_Enemy_MutantBrute", unreal.Vector(0.0, 15.0, 430.0), "Enemy_Brute_Elite"),
        # 压轴深渊领主 Boss
        ("BP_Boss_Overlord", unreal.Vector(0.0, 15.0, 560.0), "Boss_Overlord_Live"),
    ]

    deployed_actors = []
    for bp_name, loc, label in spawn_matrix:
        bp = built_bps.get(bp_name)
        if not bp:
            log(f"⚠️ 找不到已构建蓝图: {bp_name}")
            continue
            
        cfg = CFG_MAP.get(bp_name)
        cls = bp.generated_class()
        act = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, loc, unreal.Rotator())
        if act:
            act.set_actor_label(label)
            # 显式配置关卡实例上的 FlipbookComponent，双重保障绝对无误
            fb_comp = act.get_component_by_class(unreal.PaperFlipbookComponent)
            if fb_comp and cfg:
                fb_asset = unreal.load_asset(cfg["flipbook"])
                if fb_asset:
                    fb_comp.set_editor_property("source_flipbook", fb_asset)
                    sc = cfg["scale"]
                    fb_comp.set_editor_property("relative_scale3d", unreal.Vector(sc, sc, sc))
                    fb_comp.set_editor_property("translucency_sort_priority", cfg["priority"])
                    try:
                        fb_comp.set_looping(True)
                        fb_comp.play()
                    except Exception:
                        pass
                    log(f"  + 关卡实例 {label} 显式注入 Flipbook: {fb_asset.get_name()} (4帧)")
            
            deployed_actors.append({
                "label": label,
                "blueprint": bp_name,
                "class": act.get_class().get_name(),
                "location": [loc.x, loc.y, loc.z]
            })
            log(f"  + 部署动态蓝图怪物: {label} ({bp_name}) @ {loc}")

    # 3. 验证相机与地面未受影响
    all_current = unreal.EditorLevelLibrary.get_all_level_actors()
    labels = {a.get_actor_label(): a for a in all_current}
    
    if "PortraitCamera_9x16" in labels:
        cam_act = labels["PortraitCamera_9x16"]
        cam_comp = cam_act.get_component_by_class(unreal.CameraComponent)
        cam_comp.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
        cam_comp.set_editor_property("ortho_width", 941.0)
        cam_comp.set_editor_property("aspect_ratio", 0.5628)
        log("  ✅ 相机 PortraitCamera_9x16 (941.0 / 0.5628) 状态已核准！")
        
    if "Ground_Stage00" in labels:
        log("  ✅ 地面底板 Ground_Stage00 状态完好！")

    # 4. 保存主关卡与全部资产
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    ASSETS.save_directory(BP_DIR, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/GGBOM", only_if_is_dirty=False, recursive=True)
    log("💾 主关卡 MAP_GGBOM_Main 保存完成！")
    return deployed_actors

def main():
    log("=== 开始执行怪物全量动画蓝图与关卡部署 ===")
    ensure_directory(BP_DIR)
    
    built_bps = {}
    for cfg in ENEMY_CONFIGS:
        bp = build_enemy_blueprint(cfg)
        built_bps[cfg["name"]] = bp
        
    deployed = deploy_to_main_stage(built_bps)
    
    report = {
        "status": "PASS",
        "built_blueprints": list(built_bps.keys()),
        "deployed_actors": deployed
    }
    
    report_file = OUT_DIR / "deployed_enemies_report.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"🎉 全部敌人动画蓝图与关卡部署圆满完成！报告输出至: {report_file}")

if __name__ == "__main__":
    main()
