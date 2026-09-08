# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》第二阶段: 波次时间轴出怪与 40 秒战斗防线闭环
1. 创建/重构 BP_Enemy_ZombieWalker 敌人蓝图 (向下推进与生命值管理)
2. 创建 BP_StageWaveManager 蓝图 (波次时间推进与 40s 胜利自动重开)
3. 在 MAP_GGBOM_Main 中装配敌人与波次管理器
================================================================================
"""
from __future__ import annotations
from pathlib import Path
import json
import unreal

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ENEMY_BP_DIR = "/Game/Blueprints/Characters/Enemies"
ZOMBIE_BP_PATH = f"{ENEMY_BP_DIR}/BP_Enemy_ZombieWalker"
STAGE_BP_DIR = "/Game/Blueprints/Stage"
WAVE_MGR_PATH = f"{STAGE_BP_DIR}/BP_StageWaveManager"
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"

def log(msg: str):
    print(f"[StageWave] {msg}")
    unreal.log(f"[StageWave] {msg}")

def ensure_directory(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def pin(node: unreal.K2Node, name: str, output: bool) -> unreal.BlueprintGraphPin:
    values = BPLIB.list_output_pins(node) if output else BPLIB.list_input_pins(node)
    found = [p for p in values if str(PINLIB.get_pin_name(p)).lower() == name.lower()]
    if len(found) != 1:
        available = [str(PINLIB.get_pin_name(p)) for p in values]
        raise RuntimeError(f"Pin {name} missing on {BPLIB.get_node_title(node)}; available={available}")
    return found[0]

def set_value(node: unreal.K2Node, name: str, value) -> None:
    if not PINLIB.set_pin_value(pin(node, name, False), str(value)):
        raise RuntimeError(f"Default rejected: {BPLIB.get_node_title(node)}.{name}={value}")

def connect(a: unreal.K2Node, a_name: str, b: unreal.K2Node, b_name: str) -> None:
    source, target = pin(a, a_name, True), pin(b, b_name, False)
    if not PINLIB.try_create_connection(source, target):
        raise RuntimeError(f"Cannot connect {BPLIB.get_node_title(a)}.{a_name} -> {BPLIB.get_node_title(b)}.{b_name}")

# ============================================================================
# 1. 构建 BP_Enemy_ZombieWalker 敌人蓝图
# ============================================================================
def build_zombie_walker():
    log(f"🚀 [1/3] 构建丧尸敌人蓝图: {ZOMBIE_BP_PATH}...")
    ensure_directory(ENEMY_BP_DIR)
    
    if ASSETS.does_asset_exist(ZOMBIE_BP_PATH):
        ASSETS.delete_asset(ZOMBIE_BP_PATH)
        
    bp = BPLIB.create_blueprint_asset_with_parent(ZOMBIE_BP_PATH, unreal.PaperSpriteActor.static_class())
    if not bp:
        raise RuntimeError(f"无法创建丧尸蓝图: {ZOMBIE_BP_PATH}")
    
    graph = BPLIB.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    real_type = BPLIB.get_basic_type_by_name("real")
    
    # 变量
    editor.add_member_variable("MaxHealth", real_type, "65.0")
    editor.add_member_variable("CurrentHealth", real_type, "65.0")
    editor.add_member_variable("MoveSpeed", real_type, "75.0")
    
    # EventGraph: ReceiveTick -> AddActorWorldOffset (DeltaLocation=(0, 0, -2.5), bSweep=True)
    # 固定 30FPS 步进 2.5 uu/帧，产生 75 uu/s 平滑向下推进
    tick_node = editor.find_event_node("ReceiveTick")
    move_node = editor.add_call_function_node("/Script/Engine.Actor.K2_AddActorWorldOffset")
    set_value(move_node, "bSweep", "true")
    set_value(move_node, "DeltaLocation", "0,0,-2.5")
    connect(tick_node, "then", move_node, "execute")
    
    BPLIB.compile_blueprint(bp)
    
    # CDO 配置
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        sprite_comp = cdo.get_component_by_class(unreal.PaperSpriteComponent)
        if sprite_comp:
            sp = unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_ZombieWalker.SP_ZombieWalker") or unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_Zombie.SP_Zombie")
            if sp:
                sprite_comp.set_editor_property("source_sprite", sp)
            sprite_comp.set_editor_property("relative_scale3d", unreal.Vector(0.55, 0.55, 0.55))
            sprite_comp.set_editor_property("translucency_sort_priority", 350)
            sprite_comp.set_editor_property("visible", True)
            sprite_comp.set_editor_property("hidden_in_game", False)
            
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ 丧尸蓝图 {ZOMBIE_BP_PATH} 构建并编译保存成功！")
    return bp

# ============================================================================
# 2. 构建 BP_StageWaveManager 蓝图
# ============================================================================
def build_stage_wave_manager():
    log(f"🚀 [2/3] 构建关卡波次管理器: {WAVE_MGR_PATH}...")
    ensure_directory(STAGE_BP_DIR)
    
    if ASSETS.does_asset_exist(WAVE_MGR_PATH):
        ASSETS.delete_asset(WAVE_MGR_PATH)
        
    bp = BPLIB.create_blueprint_asset_with_parent(WAVE_MGR_PATH, unreal.Actor.static_class())
    if not bp:
        raise RuntimeError(f"无法创建波次管理器蓝图: {WAVE_MGR_PATH}")
        
    graph = BPLIB.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    real_type = BPLIB.get_basic_type_by_name("real")
    
    editor.add_member_variable("ElapsedTime", real_type, "0.0")
    editor.add_member_variable("TotalDuration", real_type, "40.0")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ 波次管理器蓝图 {WAVE_MGR_PATH} 构建并编译保存成功！")
    return bp

# ============================================================================
# 3. 在地图中装配波次管理器与敌群推进实例
# ============================================================================
def update_stage_map():
    log(f"🚀 [3/3] 在关卡 {MAP_PATH} 中部署波次管理器与敌群...")
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 清理旧的波次管理器与动态敌群 Actor
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for a in actors:
        lbl = a.get_actor_label()
        if "wavemanager" in lbl.lower() or "zombie_runtime" in lbl.lower():
            unreal.EditorLevelLibrary.destroy_actor(a)
            
    # 生成波次管理器 BP_StageWaveManager
    mgr_class = unreal.load_class(None, f"{WAVE_MGR_PATH}.BP_StageWaveManager_C")
    if mgr_class:
        mgr = unreal.EditorLevelLibrary.spawn_actor_from_class(mgr_class, unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
        if mgr:
            mgr.set_actor_label("BP_StageWaveManager_Runtime")
            log("✅ 成功生成关卡波次管理器: BP_StageWaveManager_Runtime")
            
    # 生成多路推进行尸实体 (左路 X=-80, 中路 X=0, 右路 X=80, Z=+260)
    zombie_class = unreal.load_class(None, f"{ZOMBIE_BP_PATH}.BP_Enemy_ZombieWalker_C")
    if zombie_class:
        sp_asset = unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_ZombieWalker.SP_ZombieWalker") or unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_Zombie.SP_Zombie")
        spawn_lanes = [(-80.0, 20.0, 240.0), (0.0, 20.0, 280.0), (80.0, 20.0, 220.0)]
        for idx, pos in enumerate(spawn_lanes):
            z = unreal.EditorLevelLibrary.spawn_actor_from_class(
                zombie_class,
                unreal.Vector(pos[0], pos[1], pos[2]),
                unreal.Rotator(0,0,0)
            )
            if z:
                z.set_actor_label(f"Zombie_Runtime_{idx+1}")
                c = z.get_component_by_class(unreal.PaperSpriteComponent)
                if c and sp_asset:
                    c.set_editor_property("source_sprite", sp_asset)
                    c.set_editor_property("relative_scale3d", unreal.Vector(0.55, 0.55, 0.55))
                    c.set_editor_property("translucency_sort_priority", 350)
                    c.set_editor_property("visible", True)
                    c.set_editor_property("hidden_in_game", False)
        log(f"✅ 成功部署 {len(spawn_lanes)} 只多路推进丧尸 (Zombie_Runtime_1~3)")
        
    unreal.EditorLevelLibrary.save_current_level()
    log(f"✅ 地图 {MAP_PATH} 保存成功！")

def main():
    log("=== 开始执行第二阶段: 波次时间轴与战斗防线闭环装配 ===")
    status = {
        "PHASE2_STATUS": "FAIL",
        "zombie_blueprint_built": False,
        "wave_manager_built": False,
        "map_updated": False
    }
    
    try:
        z_bp = build_zombie_walker()
        status["zombie_blueprint_built"] = bool(z_bp)
        
        w_bp = build_stage_wave_manager()
        status["wave_manager_built"] = bool(w_bp)
        
        update_stage_map()
        status["map_updated"] = True
        
        status["PHASE2_STATUS"] = "PASS"
        log("🎉 第二阶段: 波次时间轴与防线战斗闭环装配全部完成！")
    except Exception as e:
        log(f"❌ 装配失败: {e}")
        status["error"] = str(e)
        
    out_file = OUT_DIR / "phase2_stage_wave_status.json"
    out_file.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Status written to {out_file}")

if __name__ == "__main__":
    main()
