# -*- coding: utf-8 -*-
"""
fix_player_medic_movement.py
================================================================================
彻底修复玩家主角 BP_Player_Medic 不能移动的问题：
1. 修正移动轴向：
   - D / Right 键 -> X = +1.0 (向右)
   - A / Left  键 -> X = -1.0 (向左)
   - W / Up    键 -> Z = +1.0 (向上)
   - S / Down  键 -> Z = -1.0 (向下)
2. 双重按键支持：同时监听 W/A/S/D 与 方向键 (Up/Down/Left/Right)；
3. 彻底解除 bSweep 物理截断死锁：AddActorWorldOffset 的 bSweep 设为 False；
4. 零向量保护：未按键时直接输出 (0, 0, 0)，避免 Normal(0,0,0) 产生的物理停滞或异常；
5. 正确设置 Player0 的 AutoReceiveInput 与 AutoPossessPlayer；
6. 编译并保存 BP_Player_Medic 与相关资产。
================================================================================
"""
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

PLAYER_PATH = "/Game/Blueprints/Player/BP_Player_Medic"

def log(msg):
    print(f"[FIX_PLAYER_MOVE] {msg}", flush=True)

def pin(node, name, output=None):
    if output is True: pins = BPLIB.list_output_pins(node)
    elif output is False: pins = BPLIB.list_input_pins(node)
    else: pins = list(BPLIB.list_output_pins(node)) + list(BPLIB.list_input_pins(node))
    wanted = name.lower()
    for p in pins:
        if str(PINLIB.get_pin_name(p)).lower() == wanted: return p
    avail = [str(PINLIB.get_pin_name(p)) for p in pins]
    raise RuntimeError(f"Pin '{name}' not found, avail: {avail}")

def set_val(node, name, val):
    p = pin(node, name, False)
    PINLIB.set_pin_value(p, str(val))

def connect(n1, p1, n2, p2):
    sp = pin(n1, p1, True); tp = pin(n2, p2, False)
    return PINLIB.try_create_connection(sp, tp)

def fn(ed, path, x, y):
    n = ed.add_call_function_node(path)
    n.set_node_pos(unreal.IntPoint(x, y))
    return n

def build_safe_sample_move_input(bp):
    log("  🔨 构建兼具 WASD 与方向键的安全移动输入采样函数 (SampleMoveInput)...")
    # 清理重建该函数
    if "SampleMoveInput" in [str(x) for x in BPLIB.list_graph_names(bp)]:
        BPLIB.remove_function_graph(bp, "SampleMoveInput")
    ed = unreal.BlueprintGraphEditor.create_and_edit_function_graph(bp, "SampleMoveInput")
    start_pin = ed.find_graph_entry_pin()

    pc = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_val(pc, "PlayerIndex", 0)

    # 1. 监听 8 个按键: (A, Left), (D, Right), (W, Up), (S, Down)
    key_configs = [
        ("A", "Left", -1.0, "X", 220, -300),   # 向左
        ("D", "Right", 1.0, "X", 220, -100),   # 向右
        ("W", "Up", 1.0, "Z", 220, 100),       # 向上
        ("S", "Down", -1.0, "Z", 220, 300),    # 向下
    ]

    x_adds = []
    z_adds = []

    for k1, k2, val, axis, base_x, base_y in key_configs:
        # Key 1 检测
        node_k1 = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", base_x, base_y)
        set_val(node_k1, "Key", k1)
        connect(pc, "ReturnValue", node_k1, "self")

        # Key 2 检测
        node_k2 = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", base_x, base_y + 80)
        set_val(node_k2, "Key", k2)
        connect(pc, "ReturnValue", node_k2, "self")

        # OR 逻辑
        node_or = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", base_x + 220, base_y + 40)
        connect(node_k1, "ReturnValue", node_or, "A")
        connect(node_k2, "ReturnValue", node_or, "B")

        # SelectFloat: 按下选 val, 未按选 0.0
        node_sel = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", base_x + 400, base_y + 40)
        set_val(node_sel, "A", val)
        set_val(node_sel, "B", 0.0)
        connect(node_or, "ReturnValue", node_sel, "bPickA")

        if axis == "X":
            x_adds.append(node_sel)
        else:
            z_adds.append(node_sel)

    # 合成 X: Left + Right
    add_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 880, -200)
    connect(x_adds[0], "ReturnValue", add_x, "A")
    connect(x_adds[1], "ReturnValue", add_x, "B")

    # 合成 Z: Up + Down
    add_z = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 880, 200)
    connect(z_adds[0], "ReturnValue", add_z, "A")
    connect(z_adds[1], "ReturnValue", add_z, "B")

    # 合成 RawVector (X, 0, Z)
    raw_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1100, 0)
    connect(add_x, "ReturnValue", raw_vec, "X")
    set_val(raw_vec, "Y", 0.0)
    connect(add_z, "ReturnValue", raw_vec, "Z")

    # 判断向量是否接近零 (IsNearlyZero)
    is_zero = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_IsNearlyZero", 1320, 100)
    connect(raw_vec, "ReturnValue", is_zero, "A")
    set_val(is_zero, "Tolerance", 0.001)

    # 归一化: SafeNormal
    safe_norm = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 1320, -50)
    connect(raw_vec, "ReturnValue", safe_norm, "A")

    # 缩放步长 (恒定 7.5 uu / 帧)
    scaled_vec = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1540, -50)
    connect(safe_norm, "ReturnValue", scaled_vec, "A")
    set_val(scaled_vec, "B", 7.5)

    # 零向量保护选择: if is_zero then (0,0,0) else scaled_vec
    zero_const = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1540, 150)
    set_val(zero_const, "X", 0.0)
    set_val(zero_const, "Y", 0.0)
    set_val(zero_const, "Z", 0.0)

    final_vec = fn(ed, "/Script/Engine.KismetMathLibrary.SelectVector", 1760, 0)
    connect(zero_const, "ReturnValue", final_vec, "A")
    connect(scaled_vec, "ReturnValue", final_vec, "B")
    connect(is_zero, "ReturnValue", final_vec, "bPickA")

    # 存入 MoveInput
    set_move = ed.add_set_member_variable_node("MoveInput")
    set_move.set_node_pos(unreal.IntPoint(1980, 0))
    PINLIB.try_create_connection(start_pin, pin(set_move, "execute", False))
    connect(final_vec, "ReturnValue", set_move, "MoveInput")
    log("    ✅ SampleMoveInput 构建完成！")

def fix_event_graph_sweep(bp):
    log("  🔨 检查并解除 EventGraph 中 AddActorWorldOffset 的 bSweep 物理锁定...")
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    for n in ed.list_all_nodes():
        title = BPLIB.get_node_title(n)
        if "Add Actor World Offset" in title or "K2_AddActorWorldOffset" in str(n):
            set_val(n, "bSweep", "false")
            log(f"    🔓 已将 {title} 的 bSweep 强制设为 False！")

def run():
    log("🚀 开始修复 BP_Player_Medic 角色移动系统...")
    bp = ASSETS.load_asset(PLAYER_PATH)
    if not bp:
        raise RuntimeError("未找到 BP_Player_Medic 资产！")

    # 1. 确保 AutoReceiveInput 与 AutoPossessPlayer
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        cdo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
        cdo.set_editor_property("auto_receive_input", unreal.AutoReceiveInput.PLAYER0)
        log("  🎮 CDO 已设定 auto_possess_player 与 auto_receive_input 为 PLAYER0")

    # 2. 重新构建移动采样函数
    build_safe_sample_move_input(bp)

    # 3. 彻底解除 bSweep 物理碰撞锁死
    fix_event_graph_sweep(bp)

    # 4. 编译与保存
    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp)
    log(f"💾 BP_Player_Medic 移动修复保存状态: {saved}")
    out = ROOT / "output/player_move_fix_result.txt"
    out.write_text(f"SAVED: {saved}\n", encoding="utf-8")

if __name__ == "__main__":
    run()
