# -*- coding: utf-8 -*-
"""
变异猎犬 (BP_Enemy_MutantHound) 独立装配脚本
- 移除 ProjectileMovementComponent
- 4 向完整移动奔跑动画 (Run: Down, Right, Up, Left)
- 近身扑击技能 (Pounce: Down)
- 轴分离物理阻挡寻路 (X+Z bSweep=True)
- 实体碰撞盒 (30, 70, 32)
"""
import unreal

bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
bp = unreal.load_asset(bp_path)
if not bp:
    raise RuntimeError(f"Cannot load {bp_path}")

bplib = unreal.BlueprintEditorLibrary
pinlib = unreal.BlueprintGraphPinLibrary
subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

# 1. 移除旧的 ProjectileMovementComponent
handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)
for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    if isinstance(obj, unreal.ProjectileMovementComponent):
        subsystems.delete_subobject(handles[0], h, bp)
        break

# 2. 确保实体碰撞盒
target_comp = None
for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    if isinstance(obj, unreal.BoxComponent):
        target_comp = obj
        break
if target_comp:
    target_comp.set_editor_property("box_extent", unreal.Vector(30.0, 70.0, 32.0))
    try:
        target_comp.set_editor_property("generate_overlap_events", True)
    except Exception:
        pass

# 3. 清理 EventGraph
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

HOUND_ART_DIR = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound"
fb_run_down = unreal.load_asset(f"{HOUND_ART_DIR}/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet.FB_T_Hound_Run_Dir_01_Down_Sheet")
fb_run_right = unreal.load_asset(f"{HOUND_ART_DIR}/Run/Dir_02_Right/Flipbooks/FB_T_Hound_Run_Dir_02_Right_Sheet.FB_T_Hound_Run_Dir_02_Right_Sheet")
fb_run_up = unreal.load_asset(f"{HOUND_ART_DIR}/Run/Dir_03_Up/Flipbooks/FB_T_Hound_Run_Dir_03_Up_Sheet.FB_T_Hound_Run_Dir_03_Up_Sheet")
fb_run_left = unreal.load_asset(f"{HOUND_ART_DIR}/Run/Dir_04_Left/Flipbooks/FB_T_Hound_Run_Dir_04_Left_Sheet.FB_T_Hound_Run_Dir_04_Left_Sheet")
fb_pounce_down = unreal.load_asset(f"{HOUND_ART_DIR}/Pounce/Dir_01_Down/Flipbooks/FB_T_Hound_Pounce_Dir_01_Down_Sheet.FB_T_Hound_Pounce_Dir_01_Down_Sheet")

# 4. 采样与追逐向量
get_player = fn("/Script/Engine.GameplayStatics.GetPlayerPawn", 200, 100)
set_value(get_player, "PlayerIndex", 0)

p_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", 450, 50)
connect(get_player, "ReturnValue", p_loc, "self")

self_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", 450, 180)

dist_node = fn("/Script/Engine.KismetMathLibrary.Vector_Distance", 700, -80)
connect(p_loc, "ReturnValue", dist_node, "v1")
connect(self_loc, "ReturnValue", dist_node, "v2")

sub_v = fn("/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 100)
connect(p_loc, "ReturnValue", sub_v, "A")
connect(self_loc, "ReturnValue", sub_v, "B")

norm_v = fn("/Script/Engine.KismetMathLibrary.Normal", 920, 100)
connect(sub_v, "ReturnValue", norm_v, "A")

break_v = fn("/Script/Engine.KismetMathLibrary.BreakVector", 1140, 100)
connect(norm_v, "ReturnValue", break_v, "InVec")

speed = 150.0  # 猎犬高速冲锋

# 5. 轴分离物理位移 (X + Z 双路 Sweep)
mul_x_speed = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1360, 50)
connect(break_v, "X", mul_x_speed, "A"); set_value(mul_x_speed, "B", speed)

mul_x_dt = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1580, 50)
connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

delta_vec_x = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1800, 50)
connect(mul_x_dt, "ReturnValue", delta_vec_x, "X"); set_value(delta_vec_x, "Y", 0.0); set_value(delta_vec_x, "Z", 0.0)

move_x = fn("/Script/Engine.Actor.K2_AddActorWorldOffset", 2050, 50)
set_value(move_x, "bSweep", "true")
connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
connect(tick_node, "then", move_x, "execute")

mul_z_speed = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1360, 220)
connect(break_v, "Z", mul_z_speed, "A"); set_value(mul_z_speed, "B", speed)

mul_z_dt = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1580, 220)
connect(mul_z_speed, "ReturnValue", mul_z_dt, "A")
connect(tick_node, "DeltaSeconds", mul_z_dt, "B")

delta_vec_z = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1800, 220)
set_value(delta_vec_z, "X", 0.0); set_value(delta_vec_z, "Y", 0.0); connect(mul_z_dt, "ReturnValue", delta_vec_z, "Z")

move_z = fn("/Script/Engine.Actor.K2_AddActorWorldOffset", 2050, 220)
set_value(move_z, "bSweep", "true")
connect(delta_vec_z, "ReturnValue", move_z, "DeltaLocation")
connect(move_x, "then", move_z, "execute")

# 6. 获取 FlipbookComponent
get_fb = fn("/Script/Engine.Actor.GetComponentByClass", 1800, -250)
set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

# 7. 距离判定：扑击技能 (Dist <= 110) vs 4 向奔跑 (Dist > 110)
is_near = fn("/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 950, -80)
connect(dist_node, "ReturnValue", is_near, "A"); set_value(is_near, "B", 110.0)

br_state = ed.add_branch_node()
br_state.set_node_pos(unreal.IntPoint(2300, 100))
connect(move_z, "then", br_state, "execute")
connect(is_near, "ReturnValue", br_state, "Condition")

# 技能分支 (True): 播放扑击技能动作
set_pounce = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2550, -50)
if fb_pounce_down: set_value(set_pounce, "NewFlipbook", f"PaperFlipbook'{fb_pounce_down.get_path_name()}'")
connect(br_state, "then", set_pounce, "execute")
connect(get_fb, "ReturnValue", set_pounce, "self")

# 4 向奔跑移动分支 (False)
abs_x = fn("/Script/Engine.KismetMathLibrary.Abs", 1360, -20)
connect(break_v, "X", abs_x, "A")

abs_z = fn("/Script/Engine.KismetMathLibrary.Abs", 1360, 40)
connect(break_v, "Z", abs_z, "A")

is_horizontal = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1580, 0)
connect(abs_x, "ReturnValue", is_horizontal, "A")
connect(abs_z, "ReturnValue", is_horizontal, "B")

br_horiz = ed.add_branch_node(); br_horiz.set_node_pos(unreal.IntPoint(1800, 50))
connect(br_state, "else", br_horiz, "execute")
connect(is_horizontal, "ReturnValue", br_horiz, "Condition")

# 水平分支 (True)
is_right = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 2000, -80)
connect(break_v, "X", is_right, "A"); set_value(is_right, "B", 0.0)

br_right = ed.add_branch_node(); br_right.set_node_pos(unreal.IntPoint(2200, -80))
connect(br_horiz, "then", br_right, "execute")
connect(is_right, "ReturnValue", br_right, "Condition")

set_run_r = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2450, -120)
if fb_run_right: set_value(set_run_r, "NewFlipbook", f"PaperFlipbook'{fb_run_right.get_path_name()}'")
connect(br_right, "then", set_run_r, "execute"); connect(get_fb, "ReturnValue", set_run_r, "self")

set_run_l = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2450, -20)
if fb_run_left: set_value(set_run_l, "NewFlipbook", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
connect(br_right, "else", set_run_l, "execute"); connect(get_fb, "ReturnValue", set_run_l, "self")

# 垂直分支 (False)
is_up = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 2000, 150)
connect(break_v, "Z", is_up, "A"); set_value(is_up, "B", 0.0)

br_up = ed.add_branch_node(); br_up.set_node_pos(unreal.IntPoint(2200, 150))
connect(br_horiz, "else", br_up, "execute")
connect(is_up, "ReturnValue", br_up, "Condition")

set_run_u = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2450, 100)
if fb_run_up: set_value(set_run_u, "NewFlipbook", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
connect(br_up, "then", set_run_u, "execute"); connect(get_fb, "ReturnValue", set_run_u, "self")

set_run_d = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2450, 200)
if fb_run_down: set_value(set_run_d, "NewFlipbook", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
connect(br_up, "else", set_run_d, "execute"); connect(get_fb, "ReturnValue", set_run_d, "self")

cdo = unreal.get_default_object(bp.generated_class())
if cdo:
    comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
    if comp:
        if fb_run_down: comp.set_editor_property("source_flipbook", fb_run_down)
        comp.set_editor_property("relative_scale3d", unreal.Vector(0.48, 0.48, 0.48))
        comp.set_editor_property("translucency_sort_priority", 200)

compiled = bplib.compile_blueprint(bp)
saved = unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
print(f"HOUND_BUILD_STATUS: compiled={compiled}, saved={saved}")
