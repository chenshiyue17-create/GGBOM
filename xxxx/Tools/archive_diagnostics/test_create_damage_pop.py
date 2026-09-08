# -*- coding: utf-8 -*-
"""
test_create_damage_pop.py
构建极速轻量伤害飘字蓝图 BP_Combat_DamagePop
"""
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/create_damage_pop_result.txt"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def log(msg):
    unreal.log(f"[DAMAGE_POP] {msg}")
    print(f"[DAMAGE_POP] {msg}", flush=True)

def pin(node, name, output=None):
    if output is True: pins = BPLIB.list_output_pins(node)
    elif output is False: pins = BPLIB.list_input_pins(node)
    else: pins = list(BPLIB.list_output_pins(node)) + list(BPLIB.list_input_pins(node))
    wanted = name.lower()
    for p in pins:
        if str(PINLIB.get_pin_name(p)).lower() == wanted: return p
    avail = [str(PINLIB.get_pin_name(p)) for p in pins]
    raise RuntimeError(f"Pin '{name}' not found, avail: {avail}")

def set_value(node, name, value):
    p = pin(node, name, False)
    PINLIB.set_pin_value(p, str(value))

def connect(n1, p1, n2, p2):
    sp = pin(n1, p1, True); tp = pin(n2, p2, False)
    PINLIB.try_create_connection(sp, tp)

def run():
    bp_path = "/Game/Blueprints/Combat/Projectiles/BP_Combat_DamagePop"
    log(f"📝 构建伤害飘字蓝图: {bp_path}")
    
    # 若存在则直接加载，不存在则创建
    if ASSETS.does_asset_exist(bp_path):
        bp = ASSETS.load_asset(bp_path)
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(bp_path, unreal.TextRenderActor.static_class())
    
    if not bp:
        raise RuntimeError(f"无法创建/加载: {bp_path}")

    # 获取 CDO 配置 TextRenderComponent 默认样式
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        text_comp = cdo.get_component_by_class(unreal.TextRenderComponent)
        if text_comp:
            text_comp.set_editor_property("text", unreal.Text("-45"))
            text_comp.set_editor_property("world_size", 32.0)
            text_comp.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
            text_comp.set_editor_property("vertical_alignment", unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
            text_comp.set_editor_property("text_render_color", unreal.Color(255, 220, 40, 255)) # 亮黄色暴击感
            text_comp.set_editor_property("translucency_sort_priority", 3500) # 置于最前层
            log("  ✨ TextRenderComponent 默认属性配置就绪")

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    tick_node = ed.find_event_node("ReceiveTick")
    begin_node = ed.find_event_node("ReceiveBeginPlay")
    
    keep = set()
    if tick_node: keep.add(tick_node)
    if begin_node: keep.add(begin_node)
    
    to_remove = [n for n in ed.list_all_nodes() if n not in keep]
    if to_remove: ed.remove_nodes(to_remove)

    def fn(path, x, y):
        n = ed.add_call_function_node(path); n.set_node_pos(unreal.IntPoint(x, y)); return n

    # 1. ReceiveBeginPlay -> Delay(0.55) -> K2_DestroyActor
    if not begin_node:
        begin_node = BPLIB.add_event_override(bp, "ReceiveBeginPlay", unreal.IntPoint(0, 0))
    else:
        begin_node.set_node_pos(unreal.IntPoint(0, 0))
    
    delay_node = fn("/Script/Engine.KismetSystemLibrary.Delay", 240, 0)
    set_value(delay_node, "Duration", 0.55)
    connect(begin_node, "then", delay_node, "execute")

    destroy_node = fn("/Script/Engine.Actor.K2_DestroyActor", 480, 0)
    connect(delay_node, "then", destroy_node, "execute")

    # 2. ReceiveTick -> AddActorWorldOffset(DeltaLocation=(0, 0, 90.0 * DeltaSeconds))
    if not tick_node:
        tick_node = BPLIB.add_event_override(bp, "ReceiveTick", unreal.IntPoint(0, 240))
    else:
        tick_node.set_node_pos(unreal.IntPoint(0, 240))

    mul_dt = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 240, 300)
    set_value(mul_dt, "A", 90.0) # 向上飘移速度 90 uu/s
    connect(tick_node, "DeltaSeconds", mul_dt, "B")

    make_vec = fn("/Script/Engine.KismetMathLibrary.MakeVector", 460, 300)
    set_value(make_vec, "X", 0.0); set_value(make_vec, "Y", 0.0)
    connect(mul_dt, "ReturnValue", make_vec, "Z")

    move_node = fn("/Script/Engine.Actor.K2_AddActorWorldOffset", 680, 240)
    set_value(move_node, "bSweep", "false")
    connect(tick_node, "then", move_node, "execute")
    connect(make_vec, "ReturnValue", move_node, "DeltaLocation")

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 BP_Combat_DamagePop 构建与落盘: {'成功' if saved else '失败'}")
    OUT.write_text(f"SAVED: {saved}", encoding="utf-8")
    return saved

if __name__ == "__main__":
    run()
