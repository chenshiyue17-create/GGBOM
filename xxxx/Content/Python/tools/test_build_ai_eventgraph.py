# -*- coding: utf-8 -*-
import unreal

bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
bp = unreal.load_asset(bp_path)

bplib = unreal.BlueprintEditorLibrary
pinlib = unreal.BlueprintGraphPinLibrary
subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

# 1. 移除 ProjectileMovementComponent
handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)
for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    if isinstance(obj, unreal.ProjectileMovementComponent):
        subsystems.delete_subobject(handles[0], h, bp)
        print("Removed ProjectileMovementComponent")
        break

# 2. 清理 EventGraph 历史节点，只保留 ReceiveTick
graph = bplib.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

tick_node = ed.find_event_node("ReceiveTick")
keep_paths = {tick_node.get_path_name()}
begin_node = ed.find_event_node("ReceiveBeginPlay")
if begin_node:
    keep_paths.add(begin_node.get_path_name())

nodes_to_remove = [n for n in ed.list_all_nodes() if n.get_path_name() not in keep_paths]
if nodes_to_remove:
    ed.remove_nodes(nodes_to_remove)

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

def fn(path, x, y):
    node = ed.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"Cannot create node: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

# 3. 直接在 EventGraph 构建 AI 追逐逻辑
# 获取玩家
get_player = fn("/Script/Engine.GameplayStatics.GetPlayerPawn", 200, 100)
set_value(get_player, "PlayerIndex", 0)

# 获取玩家与自身坐标
p_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", 450, 50)
connect(get_player, "ReturnValue", p_loc, "self")

self_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", 450, 180)

# 计算差值向量
sub_v = fn("/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 100)
connect(p_loc, "ReturnValue", sub_v, "A")
connect(self_loc, "ReturnValue", sub_v, "B")

# 单位化向量
norm_v = fn("/Script/Engine.KismetMathLibrary.Normal", 920, 100)
connect(sub_v, "ReturnValue", norm_v, "A")

# 拆分并重建纯 2D 方向 (X, 0, Z)
break_v = fn("/Script/Engine.KismetMathLibrary.BreakVector", 1140, 100)
connect(norm_v, "ReturnValue", break_v, "InVec")

make_v = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1360, 100)
connect(break_v, "X", make_v, "X")
set_value(make_v, "Y", 0.0)
connect(break_v, "Z", make_v, "Z")

# 乘以 MoveSpeed (65.0)
mul_speed = fn("/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1580, 100)
connect(make_v, "ReturnValue", mul_speed, "A")
set_value(mul_speed, "B", 65.0)

# 乘以 DeltaSeconds
mul_dt = fn("/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1800, 100)
connect(mul_speed, "ReturnValue", mul_dt, "A")
connect(tick_node, "DeltaSeconds", mul_dt, "B")

# 执行位移 (bSweep = True)
move_node = fn("/Script/Engine.Actor.K2_AddActorWorldOffset", 2050, 50)
set_value(move_node, "bSweep", "true")
connect(mul_dt, "ReturnValue", move_node, "DeltaLocation")
connect(tick_node, "then", move_node, "execute")

# 左右视觉翻转 (玩家在右则翻转 X=-0.45，玩家在左则 X=0.45)
is_right = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1360, -100)
connect(break_v, "X", is_right, "A")
set_value(is_right, "B", 0.0)

sel_scale = fn("/Script/Engine.KismetMathLibrary.SelectFloat", 1580, -100)
set_value(sel_scale, "A", -0.45)
set_value(sel_scale, "B", 0.45)
connect(is_right, "ReturnValue", sel_scale, "bPickA")

scale_vec = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1800, -100)
connect(sel_scale, "ReturnValue", scale_vec, "X")
set_value(scale_vec, "Y", 0.45)
set_value(scale_vec, "Z", 0.45)

get_fb = fn("/Script/Engine.Actor.GetComponentByClass", 1800, -250)
set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

set_scale = fn("/Script/Engine.SceneComponent.SetRelativeScale3D", 2050, -150)
connect(get_fb, "ReturnValue", set_scale, "self")
connect(scale_vec, "ReturnValue", set_scale, "NewScale3D")
connect(move_node, "then", set_scale, "execute")

# 4. 编译与保存
compiled = bplib.compile_blueprint(bp)
saved = unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
print(f"Compilation status: {compiled}, Saved: {saved}")
unreal.log(f"ZombieWalker EventGraph AI Chase Complete: compiled={compiled}, saved={saved}")
