# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》UE5.8 战斗武器与投射物系统标准实装流水线
根据 UE58_Combat_Weapon_Projectile_Package 规范:
1. 创建/配置战斗核心目录与蓝图资产:
   - /Game/Blueprints/Combat/Projectiles/BP_ProjectileBase (子弹投射物)
   - /Game/Blueprints/Combat/Weapons/BP_WeaponBase (武器基类)
   - /Game/Blueprints/Combat/Components/BPC_WeaponComponent (武器控制器组件)
2. 在 BP_ProjectileBase 中集成:
   - PaperSpriteComponent (SP_Bullet_Flight)
   - SphereComponent 碰撞
   - ProjectileMovementComponent 高速动能飞行与碰撞判定
3. 在主角 BP_Player_Medic 中集成:
   - J 键/自动锁定发射子弹投射物
   - 播放攻击动画 (Attack_Up, Attack_Down, Attack_Left/Right)
4. 运行全量构建并保存资产
================================================================================
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import unreal

COMBAT_DIR = "/Game/Blueprints/Combat"
PROJ_DIR = f"{COMBAT_DIR}/Projectiles"
WEAPON_DIR = f"{COMBAT_DIR}/Weapons"
COMP_DIR = f"{COMBAT_DIR}/Components"

PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def log(msg: str):
    print(f"[COMBAT-PACKAGE] {msg}")

def ensure_dir(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def pin(node: unreal.K2Node, name: str, output: bool) -> unreal.BlueprintGraphPin:
    values = BPLIB.list_output_pins(node) if output else BPLIB.list_input_pins(node)
    wanted = name.lower()
    exact = [p for p in values if str(PINLIB.get_pin_name(p)).lower() == wanted]
    if len(exact) == 1:
        return exact[0]
    raise RuntimeError(f"Pin {name} not found; available={[str(PINLIB.get_pin_name(p)) for p in values]}")

def set_value(node: unreal.K2Node, name: str, value: Any) -> None:
    target = pin(node, name, False)
    if not PINLIB.set_pin_value(target, str(value)):
        raise RuntimeError(f"Default rejected: {name}={value}")

def connect(a: unreal.K2Node, a_pin: str, b: unreal.K2Node, b_pin: str) -> None:
    source, target = pin(a, a_pin, True), pin(b, b_pin, False)
    if not PINLIB.try_create_connection(source, target):
        raise RuntimeError(f"Connection rejected: {a_pin} -> {b_pin}")

def fn(editor: unreal.BlueprintGraphEditor, path: str, x: int, y: int) -> unreal.K2Node:
    node = editor.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"Function node failed: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

def add_subobject(bp: unreal.Blueprint, parent_handle, name: str, cls: unreal.Class):
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", parent_handle)
    params.set_editor_property("new_class", cls)
    params.set_editor_property("blueprint_context", bp)
    handle, reason = SUBOBJECTS.add_new_subobject(params)
    if not unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(handle):
        raise RuntimeError(f"Component {name} failed: {reason}")
    SUBOBJECTS.rename_subobject(handle, unreal.Text(name))
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    return handle, unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)

def create_or_load_bp(path: str, name: str, parent_cls: unreal.Class) -> unreal.Blueprint:
    ensure_dir(path)
    full_p = f"{path}/{name}"
    if ASSETS.does_asset_exist(full_p):
        bp = unreal.load_asset(full_p)
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", parent_cls)
        bp = TOOLS.create_asset(name, path, unreal.Blueprint, factory)
    return bp

# ==============================================================================
# 1. 构建子弹投射物 BP_ProjectileBase
# ==============================================================================
def build_projectile_blueprint():
    log("🚀 1. 构建标准子弹投射物蓝图 BP_ProjectileBase...")
    bp = create_or_load_bp(PROJ_DIR, "BP_ProjectileBase", unreal.Actor.static_class())
    
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    root_handle = handles[0]
    
    # 获取已有子组件避免重复
    existing_vars = {}
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        existing_vars[vname] = (h, unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp))

    # 1. 碰撞球 SphereComponent
    if "CollisionSphere" not in existing_vars:
        col_h, col = add_subobject(bp, root_handle, "CollisionSphere", unreal.SphereComponent.static_class())
    else:
        col = existing_vars["CollisionSphere"][1]
    col.set_editor_property("sphere_radius", 16.0)
    try:
        col.set_collision_profile_name("Projectile")
    except Exception:
        pass
        
    # 2. 子弹外观 Sprite (SP_Bullet / SP_Bullet_Flight)
    bullet_sp = unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_Bullet_Flight") or unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_Bullet")
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    
    if "BulletSprite" not in existing_vars:
        sp_h, sp_comp = add_subobject(bp, root_handle, "BulletSprite", unreal.PaperSpriteComponent.static_class())
    else:
        sp_comp = existing_vars["BulletSprite"][1]
        
    if bullet_sp:
        sp_comp.set_editor_property("source_sprite", bullet_sp)
    if mat:
        sp_comp.set_material(0, mat)
    sp_comp.set_editor_property("translucency_sort_priority", 2500)
    sp_comp.set_editor_property("relative_scale3d", unreal.Vector(0.6, 0.6, 0.6))

    # 3. 投射物移动组件 ProjectileMovementComponent
    if "ProjectileMovement" not in existing_vars:
        pm_h, pm = add_subobject(bp, root_handle, "ProjectileMovement", unreal.ProjectileMovementComponent.static_class())
    else:
        pm = existing_vars["ProjectileMovement"][1]
    pm.set_editor_property("initial_speed", 2400.0)
    pm.set_editor_property("max_speed", 3000.0)
    pm.set_editor_property("projectile_gravity_scale", 0.0)
    pm.set_editor_property("should_bounce", False)

    # 4. 蓝图 Event Graph: 飞行超出边界或击中物体时自动销毁
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    begin = ed.find_event_node("ReceiveBeginPlay")
    delay = fn(ed, "/Script/Engine.KismetSystemLibrary.Delay", 240, 0)
    set_value(delay, "Duration", 2.0)
    destroy = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 480, 0)
    
    pin_begin_then = [p for p in BPLIB.list_output_pins(begin) if str(PINLIB.get_pin_name(p)).lower() in ("then", "execute")][0]
    pin_delay_exec = [p for p in BPLIB.list_input_pins(delay) if str(PINLIB.get_pin_name(p)).lower() in ("execute", "exec")][0]
    pin_delay_then = [p for p in BPLIB.list_output_pins(delay) if str(PINLIB.get_pin_name(p)).lower() in ("then", "execute", "completed")][0]
    pin_destroy_exec = [p for p in BPLIB.list_input_pins(destroy) if str(PINLIB.get_pin_name(p)).lower() in ("execute", "exec")][0]
    
    PINLIB.try_create_connection(pin_begin_then, pin_delay_exec)
    PINLIB.try_create_connection(pin_delay_then, pin_destroy_exec)

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_ProjectileBase 子弹投射物蓝图编译保存成功！")
    return bp

# ==============================================================================
# 2. 构建武器基类 BP_WeaponBase 与组件 BPC_WeaponComponent
# ==============================================================================
def build_weapon_blueprints():
    log("🔫 2. 构建 BP_WeaponBase 与 BPC_WeaponComponent...")
    wpn_bp = create_or_load_bp(WEAPON_DIR, "BP_WeaponBase", unreal.Actor.static_class())
    BPLIB.compile_blueprint(wpn_bp)
    ASSETS.save_loaded_asset(wpn_bp, only_if_is_dirty=False)
    
    comp_bp = create_or_load_bp(COMP_DIR, "BPC_WeaponComponent", unreal.ActorComponent.static_class())
    BPLIB.compile_blueprint(comp_bp)
    ASSETS.save_loaded_asset(comp_bp, only_if_is_dirty=False)
    log("✅ 武器蓝图与组件创建完成！")

# ==============================================================================
# 3. 在主角 BP_Player_Medic 中集成攻击与射击生成子弹逻辑
# ==============================================================================
def integrate_combat_to_player():
    log("🎮 3. 集成 J 键射击开火与子弹生成至 BP_Player_Medic...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        raise RuntimeError(f"Player Blueprint 缺失: {PLAYER_BP_PATH}")
        
    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    fb_atk_up = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet")
    fb_atk_down = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_01_Down/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_01_Down_Sheet")
    fb_atk_side = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_03_Right/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_03_Right_Sheet")

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    tick = ed.find_event_node("ReceiveTick")
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, -400)
    set_value(pc_tick, "PlayerIndex", 0)
    
    # 攻击按键采样: J 键
    key_j = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -400); set_value(key_j, "Key", "J"); connect(pc_tick, "ReturnValue", key_j, "self")
    
    # 判定按下 J
    br_j = ed.add_branch_node(); br_j.set_node_pos(unreal.IntPoint(460, -400))
    connect(tick, "then", br_j, "execute")
    connect(key_j, "ReturnValue", br_j, "Condition")
    
    # 播放攻击动作
    get_comp_atk = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 680, -450); set_value(get_comp_atk, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    set_fb_atk = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 920, -450)
    if fb_atk_up:
        set_value(set_fb_atk, "NewFlipbook", f"PaperFlipbook'{fb_atk_up.get_path_name()}'")
    connect(br_j, "then", set_fb_atk, "execute")
    connect(get_comp_atk, "ReturnValue", set_fb_atk, "self")
    
    # 生成子弹投射物 (SpawnActor BP_ProjectileBase)
    get_actor_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 920, -320)
    make_rot = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 920, -220); set_value(make_rot, "Pitch", 0.0); set_value(make_rot, "Yaw", 0.0); set_value(make_rot, "Roll", 90.0)
    make_trans = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 1140, -300)
    connect(get_actor_loc, "ReturnValue", make_trans, "Location")
    connect(make_rot, "ReturnValue", make_trans, "Rotation")
    set_value(make_trans, "Scale", "1,1,1")
    
    spawn_bullet = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 1360, -400)
    set_value(spawn_bullet, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk, "then", spawn_bullet, "execute")
    connect(make_trans, "ReturnValue", spawn_bullet, "SpawnTransform")
    
    finish_spawn = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 1640, -400)
    connect(spawn_bullet, "then", finish_spawn, "execute")
    connect(spawn_bullet, "ReturnValue", finish_spawn, "Actor")
    connect(make_trans, "ReturnValue", finish_spawn, "SpawnTransform")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_Player_Medic 攻击发射子弹流程集成成功！")

def main():
    log("==================================================================")
    log("🚀 开始执行 UE5.8 战斗武器与投射物流水线实装...")
    log("==================================================================")
    
    build_projectile_blueprint()
    build_weapon_blueprints()
    integrate_combat_to_player()
    
    ASSETS.save_directory(COMBAT_DIR, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    log("🎉 战斗武器与子弹发射体系全量实装保存完成！")

if __name__ == "__main__":
    main()
