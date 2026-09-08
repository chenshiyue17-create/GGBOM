# -*- coding: utf-8 -*-
import unreal

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

bp = ASSETS.load_asset("/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord")
graph = BPLIB.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

BOSS_ART = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord"
fb_up = unreal.load_asset(f"{BOSS_ART}/Actions/Walk/Dir_03_Up/Flipbooks/FB_T_Boss_Walk_Dir_03_Up_Sheet.FB_T_Boss_Walk_Dir_03_Up_Sheet")
fb_down = unreal.load_asset(f"{BOSS_ART}/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet.FB_T_Boss_Walk_Dir_01_Down_Sheet")

sel_node = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.SelectObject")
set_fb = ed.add_call_function_node("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook")

p_a = [p for p in BPLIB.list_input_pins(sel_node) if str(PINLIB.get_pin_name(p)).lower() == "a"][0]
p_b = [p for p in BPLIB.list_input_pins(sel_node) if str(PINLIB.get_pin_name(p)).lower() == "b"][0]

PINLIB.set_pin_value(p_a, f"PaperFlipbook'{fb_up.get_path_name()}'")
PINLIB.set_pin_value(p_b, f"PaperFlipbook'{fb_down.get_path_name()}'")

sp = [p for p in BPLIB.list_output_pins(sel_node) if str(PINLIB.get_pin_name(p)).lower() == "returnvalue"][0]
tp = [p for p in BPLIB.list_input_pins(set_fb) if str(PINLIB.get_pin_name(p)).lower() == "newflipbook"][0]

ok = PINLIB.try_create_connection(sp, tp)

lines = [
    f"After set_value, SelectObject ReturnValue PinType: {PINLIB.get_pin_type(sp)}",
    f"try_create_connection: {ok}"
]
ed.remove_nodes([sel_node, set_fb])

from pathlib import Path
ROOT = Path(unreal.Paths.project_dir()).resolve()
(ROOT / "output/test_select_typed.txt").write_text("\n".join(lines), encoding="utf-8")
