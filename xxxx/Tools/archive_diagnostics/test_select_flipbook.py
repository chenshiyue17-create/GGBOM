# -*- coding: utf-8 -*-
import unreal

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

bp = ASSETS.load_asset("/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord")
graph = BPLIB.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

sel_node = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.SelectObject")
set_fb = ed.add_call_function_node("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook")

sp = [p for p in BPLIB.list_output_pins(sel_node) if str(PINLIB.get_pin_name(p)).lower() == "returnvalue"][0]
tp = [p for p in BPLIB.list_input_pins(set_fb) if str(PINLIB.get_pin_name(p)).lower() == "newflipbook"][0]

lines = []
lines.append(f"SelectObject ReturnValue PinType: {PINLIB.get_pin_type(sp)}")
lines.append(f"SetFlipbook NewFlipbook PinType: {PINLIB.get_pin_type(tp)}")
lines.append(f"try_create_connection: {ok}")

from pathlib import Path
ROOT = Path(unreal.Paths.project_dir()).resolve()
(ROOT / "output/test_select_fb.txt").write_text("\n".join(lines), encoding="utf-8")

ed.remove_nodes([sel_node, set_fb])
