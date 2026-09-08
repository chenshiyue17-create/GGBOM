# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》全量 7 类敌人自主 AI 追踪寻路与视觉朝向自适应总构建脚本
1. 移除敌人蓝图中的固定弹道 ProjectileMovementComponent
2. 在 EventGraph 中直接构建轴分离物理阻挡寻路 (Separate-Axis Swept Pursuit)
   - 目标锁定玩家主角 GetPlayerPawn(0)
   - 计算 X-Z 平面追逐向量并单位化
   - X 轴位移 (bSweep=True) + Z 轴位移 (bSweep=True)：自动绕行沙袋掩体避障
   - 视觉朝向实时左右翻转，始终面向主角
3. 覆盖全量 7 类敌人家族并编译保存
================================================================================
"""
from __future__ import annotations
import unreal

ENEMY_BP_DIR = "/Game/Blueprints/Characters/Enemies"
bplib = unreal.BlueprintEditorLibrary
pinlib = unreal.BlueprintGraphPinLibrary
subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

ENEMY_SPECS = [
    {
        "name": "BP_Enemy_ZombieWalker",
        "display": "基础感染行尸",
        "speed": 65.0,
        "scale": 0.45,
    },
    {
        "name": "BP_Enemy_ZombieRunner",
        "display": "敏捷疾跑行尸",
        "speed": 110.0,
        "scale": 0.45,
    },
    {
        "name": "BP_Enemy_MutantHound",
        "display": "疾行变异猎犬",
        "speed": 150.0,
        "scale": 0.48,
    },
    {
        "name": "BP_Enemy_VenomShooter",
        "display": "毒液喷射行尸",
        "speed": 55.0,
        "scale": 0.45,
    },
    {
        "name": "BP_Enemy_ArmoredGuard",
        "display": "重装防暴行尸",
        "speed": 50.0,
        "scale": 0.50,
    },
    {
        "name": "BP_Enemy_MutantBrute",
        "display": "重型蹒跚蛮兽",
        "speed": 40.0,
        "scale": 0.58,
    },
    {
        "name": "BP_Boss_Overlord",
        "display": "深渊异化领主 Boss",
        "speed": 30.0,
        "scale": 0.68,
    },
]

def log(msg: str):
    print(f"[EnemyAIRebuild] {msg}")
    unreal.log(f"[EnemyAIRebuild] {msg}")

def pin(node, name, output):
    values = bplib.list_output_pins(node) if output else bplib.list_input_pins(node)
    wanted = name.lower()
    exact = [p for p in values if str(pinlib.get_pin_name(p)).lower() == wanted]
    if len(exact) == 1:
        return exact[0]
    raise RuntimeError(f"Pin {name} not found; available={[str(pinlib.get_pin_name(p)) for p in values]}")

def set_value(node, name, value):
    target = pin(node, name, False)
    if not pinlib.set_pin_value(target, str(value)):
        raise RuntimeError(f"Default rejected: {name}={value}")

def connect(a, a_pin, b, b_pin):
    source, target = pin(a, a_pin, True), pin(b, b_pin, False)
    if not pinlib.try_create_connection(source, target):
        raise RuntimeError(f"Connection rejected: {a_pin} -> {b_pin}")

def fn(ed, path, x, y):
    node = ed.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"Cannot create node: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

def build_enemy_ai(spec: dict):
    bp_path = f"{ENEMY_BP_DIR}/{spec['name']}"
    log(f"🛠️ 正在重构敌人 AI 追逐图表: {spec['display']} ({bp_path})...")
    bp = unreal.load_asset(bp_path)
    if not bp:
        log(f"⚠️ 无法加载蓝图资产: {bp_path}")
        return False

    # 1. 移除旧的 ProjectileMovementComponent
    handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if isinstance(obj, unreal.ProjectileMovementComponent):
            subsystems.delete_subobject(handles[0], h, bp)
            log("  - 已清理旧的固定弹道推进组件 (ProjectileMovementComponent)")
            break

    # 2. 清理 EventGraph 历史冗余节点
    graph = bplib.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick_node = ed.find_event_node("ReceiveTick")
    begin_node = ed.find_event_node("ReceiveBeginPlay")
    keep_paths = {tick_node.get_path_name()}
    if begin_node:
        keep_paths.add(begin_node.get_path_name())

    nodes_to_remove = [n for n in ed.list_all_nodes() if n.get_path_name() not in keep_paths]
    if nodes_to_remove:
        ed.remove_nodes(nodes_to_remove)

    # 3. 构建智能追逐寻路节点
    # 获取玩家 Pawn
    get_player = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerPawn", 200, 100)
    set_value(get_player, "PlayerIndex", 0)

    # 获取坐标
    p_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 450, 50)
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 450, 180)

    # 向量相减
    sub_v = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 100)
    connect(p_loc, "ReturnValue", sub_v, "A")
    connect(self_loc, "ReturnValue", sub_v, "B")

    # 单位化方向
    norm_v = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 920, 100)
    connect(sub_v, "ReturnValue", norm_v, "A")

    # 分离 X-Z 分量 (消除 Y 深度干扰)
    break_v = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 1140, 100)
    connect(norm_v, "ReturnValue", break_v, "InVec")

    speed = spec["speed"]
    base_scale = spec["scale"]

    # --- 轴分离位移 1: X 轴位移 (步长 = DirX * Speed * dt) ---
    mul_x_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1360, 50)
    connect(break_v, "X", mul_x_speed, "A")
    set_value(mul_x_speed, "B", speed)

    mul_x_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1580, 50)
    connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

    delta_vec_x = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1800, 50)
    connect(mul_x_dt, "ReturnValue", delta_vec_x, "X")
    set_value(delta_vec_x, "Y", 0.0)
    set_value(delta_vec_x, "Z", 0.0)

    move_x = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2050, 50)
    set_value(move_x, "bSweep", "true")
    connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
    connect(tick_node, "then", move_x, "execute")

    # --- 轴分离位移 2: Z 轴位移 (步长 = DirZ * Speed * dt) ---
    mul_z_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1360, 220)
    connect(break_v, "Z", mul_z_speed, "A")
    set_value(mul_z_speed, "B", speed)

    mul_z_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1580, 220)
    connect(mul_z_speed, "ReturnValue", mul_z_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_z_dt, "B")

    delta_vec_z = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1800, 220)
    set_value(delta_vec_z, "X", 0.0)
    set_value(delta_vec_z, "Y", 0.0)
    connect(mul_z_dt, "ReturnValue", delta_vec_z, "Z")

    move_z = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2050, 220)
    set_value(move_z, "bSweep", "true")
    connect(delta_vec_z, "ReturnValue", move_z, "DeltaLocation")
    connect(move_x, "then", move_z, "execute")

    # --- 视觉朝向水平自适应翻转 (玩家在右侧 X 镜像，玩家在左侧 X 正向) ---
    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1360, -120)
    connect(break_v, "X", is_right, "A")
    set_value(is_right, "B", 0.0)

    sel_scale = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 1580, -120)
    set_value(sel_scale, "A", -base_scale)
    set_value(sel_scale, "B", base_scale)
    connect(is_right, "ReturnValue", sel_scale, "bPickA")

    scale_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1800, -120)
    connect(sel_scale, "ReturnValue", scale_vec, "X")
    set_value(scale_vec, "Y", base_scale)
    set_value(scale_vec, "Z", base_scale)

    get_fb = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1800, -260)
    set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    set_scale = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2050, -180)
    connect(get_fb, "ReturnValue", set_scale, "self")
    connect(scale_vec, "ReturnValue", set_scale, "NewScale3D")
    connect(move_z, "then", set_scale, "execute")

    # 4. 编译与保存
    compiled = bplib.compile_blueprint(bp)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  ✅ {spec['display']} AI 追逐图表装配完毕: Compiled={compiled}, Saved={saved}")
    return compiled and saved

def main():
    log("🚀 开始执行全量 7 类敌人自主 AI 追踪寻路重构...")
    success_count = 0
    for spec in ENEMY_SPECS:
        if build_enemy_ai(spec):
            success_count += 1
    log(f"🎉 敌人 AI 追逐图表重构全部完成: {success_count}/{len(ENEMY_SPECS)} 成功！")

    # 保存蓝图与资产目录
    unreal.EditorAssetLibrary.save_directory("/Game/Blueprints/Characters/Enemies", only_if_is_dirty=False, recursive=True)

if __name__ == "__main__":
    main()
