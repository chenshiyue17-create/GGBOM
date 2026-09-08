# -*- coding: utf-8 -*-
import unreal
from pathlib import Path
import traceback

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/boss_error_analysis.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def run():
    diag_f = ROOT / "Tools/diagnose_boss_error.py"
    if diag_f.exists():
        try: diag_f.unlink()
        except Exception: pass

    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"

    bp = ASSETS.load_asset(bp_path)
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    nodes = ed.list_all_nodes()

    lines = [f"=== BP_Boss_Overlord EventGraph Nodes ({len(nodes)}) ==="]

    for n in nodes:
        title = BPLIB.get_node_title(n)
        cls_name = n.get_class().get_name()
        pos = n.get_node_pos()
        
        pin_infos = []
        for p in BPLIB.list_all_pins(n):
            pname = str(PINLIB.get_pin_name(p))
            linked = PINLIB.is_pin_linked(p)
            links = []
            if linked:
                for target_pin in PINLIB.get_linked_pins(p):
                    target_node = PINLIB.get_owning_node(target_pin)
                    target_title = BPLIB.get_node_title(target_node)
                    target_pname = str(PINLIB.get_pin_name(target_pin))
                    links.append(f"{target_title}.{target_pname}")
            default_val = PINLIB.get_pin_value(p)
            pin_infos.append(f"    - Pin '{pname}' (val: '{default_val}') -> {', '.join(links) if links else 'unlinked'}")
        
        lines.append(f"\nNode [{cls_name}] \"{title}\" at ({pos.x}, {pos.y}):")
        lines.extend(pin_infos)

    # 检查子函数与宏
    lines.append(f"\n=== Blueprint Subgraphs / Functions ===")
    # 检查所有图表
    all_graphs = bp.get_editor_property("function_graphs")
    for fg in all_graphs:
        fg_name = fg.get_name()
        lines.append(f"Function Graph: {fg_name}")
        fg_ed = unreal.BlueprintGraphEditor.get_graph_editor(fg)
        for fn_node in fg_ed.list_all_nodes():
            lines.append(f"  [{fn_node.get_class().get_name()}] {BPLIB.get_node_title(fn_node)}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Analysis saved to {OUT}", flush=True)

if __name__ == "__main__":
    run()

