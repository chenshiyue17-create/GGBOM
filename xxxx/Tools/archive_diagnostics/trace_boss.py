# -*- coding: utf-8 -*-
import unreal

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

def log(msg):
    unreal.log(f"[TRACE] {msg}")
    print(f"[TRACE] {msg}", flush=True)

bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
bp = ASSETS.load_asset(bp_path)
graph = BPLIB.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
tick_node = ed.find_event_node("ReceiveTick")

def pin(node, name, output=None):
    if output is True:
        pins = BPLIB.list_output_pins(node)
    elif output is False:
        pins = BPLIB.list_input_pins(node)
    else:
        pins = list(BPLIB.list_output_pins(node)) + list(BPLIB.list_input_pins(node))
    
    wanted = name.lower()
    for p in pins:
        if str(PINLIB.get_pin_name(p)).lower() == wanted:
            return p
    avail = [str(PINLIB.get_pin_name(p)) for p in pins]
    raise RuntimeError(f"未找到引脚 '{name}'，可用引脚: {avail}")

def set_value(node, name, value):
    p = pin(node, name, False)
    if not PINLIB.set_pin_value(p, str(value)):
        raise RuntimeError(f"设置引脚默认值失败: {name}={value}")

def connect(n1, p1, n2, p2):
    sp = pin(n1, p1, True)
    tp = pin(n2, p2, False)
    ok = PINLIB.try_create_connection(sp, tp)
    if not ok:
        raise RuntimeError(f"连线失败: {BPLIB.get_node_title(n1)}.{p1} -> {BPLIB.get_node_title(n2)}.{p2}")
    return ok

def fn(path, x, y):
    log(f"Calling add_call_function_node: {path}")
    node = ed.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"创建函数节点失败: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

log("Starting boss trace...")
get_player = fn("/Script/Engine.GameplayStatics.GetPlayerPawn", 220, 100)
set_value(get_player, "PlayerIndex", 0)

p_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", 460, 40)
connect(get_player, "ReturnValue", p_loc, "self")

self_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", 460, 180)

dist_node = fn("/Script/Engine.KismetMathLibrary.Vector_Distance", 700, -80)
connect(p_loc, "ReturnValue", dist_node, "v1")
connect(self_loc, "ReturnValue", dist_node, "v2")

is_far = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 940, -80)
connect(dist_node, "ReturnValue", is_far, "A")
set_value(is_far, "B", 125.0)

br_gate = ed.add_branch_node()
connect(tick_node, "then", br_gate, "execute")
connect(is_far, "ReturnValue", br_gate, "Condition")

sub_v = fn("/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 120)
connect(p_loc, "ReturnValue", sub_v, "A")
connect(self_loc, "ReturnValue", sub_v, "B")

norm_v = fn("/Script/Engine.KismetMathLibrary.Normal", 920, 120)
connect(sub_v, "ReturnValue", norm_v, "A")

break_v = fn("/Script/Engine.KismetMathLibrary.BreakVector", 1140, 120)
connect(norm_v, "ReturnValue", break_v, "InVec")

speed = 35.0
mul_x_speed = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 40)
connect(break_v, "X", mul_x_speed, "A")
set_value(mul_x_speed, "B", speed)

mul_x_dt = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1600, 40)
connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

delta_vec_x = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1820, 40)
connect(mul_x_dt, "ReturnValue", delta_vec_x, "X")
set_value(delta_vec_x, "Y", 0.0)
set_value(delta_vec_x, "Z", 0.0)

move_x = fn("/Script/Engine.Actor.K2_AddActorWorldOffset", 2060, 40)
set_value(move_x, "bSweep", "true")
connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
connect(br_gate, "then", move_x, "execute")

mul_z_speed = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 200)
connect(break_v, "Z", mul_z_speed, "A")
set_value(mul_z_speed, "B", speed)

mul_z_dt = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1600, 200)
connect(mul_z_speed, "ReturnValue", mul_z_dt, "A")
connect(tick_node, "DeltaSeconds", mul_z_dt, "B")

delta_vec_z = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1820, 200)
set_value(delta_vec_z, "X", 0.0)
set_value(delta_vec_z, "Y", 0.0)
connect(mul_z_dt, "ReturnValue", delta_vec_z, "Z")

move_z = fn("/Script/Engine.Actor.K2_AddActorWorldOffset", 2060, 200)
set_value(move_z, "bSweep", "true")
connect(delta_vec_z, "ReturnValue", move_z, "DeltaLocation")
connect(move_x, "then", move_z, "execute")

get_fb = fn("/Script/Engine.Actor.GetComponentByClass", 1820, -260)
set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

abs_x = fn("/Script/Engine.KismetMathLibrary.Abs", 1380, -40)
connect(break_v, "X", abs_x, "A")
abs_z = fn("/Script/Engine.KismetMathLibrary.Abs", 1380, 10)
connect(break_v, "Z", abs_z, "A")

is_horizontal = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1600, -20)
connect(abs_x, "ReturnValue", is_horizontal, "A")
connect(abs_z, "ReturnValue", is_horizontal, "B")

br_axis = ed.add_branch_node()
connect(move_z, "then", br_axis, "execute")
connect(is_horizontal, "ReturnValue", br_axis, "Condition")

is_right = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1820, -40)
connect(break_v, "X", is_right, "A")
set_value(is_right, "B", 0.0)

br_horiz = ed.add_branch_node()
connect(br_axis, "then", br_horiz, "execute")
connect(is_right, "ReturnValue", br_horiz, "Condition")

set_right = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2800, -100)
connect(br_horiz, "then", set_right, "execute")
connect(get_fb, "ReturnValue", set_right, "self")

set_left = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2800, 20)
connect(br_horiz, "else", set_left, "execute")
connect(get_fb, "ReturnValue", set_left, "self")

is_up = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1820, 80)
connect(break_v, "Z", is_up, "A")
set_value(is_up, "B", 0.0)

br_vert = ed.add_branch_node()
connect(br_axis, "else", br_vert, "execute")
connect(is_up, "ReturnValue", br_vert, "Condition")

set_up = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2800, 120)
connect(br_vert, "then", set_up, "execute")
connect(get_fb, "ReturnValue", set_up, "self")

set_down = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2800, 240)
connect(br_vert, "else", set_down, "execute")
connect(get_fb, "ReturnValue", set_down, "self")

set_slam = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 1400, -200)
connect(br_gate, "else", set_slam, "execute")
connect(get_fb, "ReturnValue", set_slam, "self")

log("🎉 All Boss nodes created and connected successfully!")
