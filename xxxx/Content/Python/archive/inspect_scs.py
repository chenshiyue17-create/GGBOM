# -*- coding: utf-8 -*-
import unreal

bp_path = "/Game/Blueprints/Player/BP_Player_Medic"
bp = unreal.load_asset(bp_path)
out_lines = []

if bp:
    out_lines.append(f"=== BLUEPRINT: {bp.get_path_name()} ===")
    scs = bp.simple_construction_script
    if scs:
        nodes = scs.get_all_nodes()
        out_lines.append(f"Total SCS Nodes: {len(nodes)}")
        for node in nodes:
            comp_class = node.component_class.get_name() if node.component_class else "None"
            var_name = node.get_variable_name()
            out_lines.append(f"  SCS Node: var_name='{var_name}', comp_class='{comp_class}'")
            if comp_class == "PaperFlipbookComponent":
                comp_template = node.component_template
                if comp_template:
                    fb = comp_template.get_editor_property("source_flipbook")
                    fb_name = fb.get_name() if fb else "None"
                    vis = comp_template.get_editor_property("visible")
                    loc = comp_template.get_editor_property("relative_location")
                    scale = comp_template.get_editor_property("relative_scale3d")
                    out_lines.append(f"    -> Flipbook: {fb_name} | Vis: {vis} | Loc: {loc} | Scale: {scale}")

# 检查 /Game/GGBOM/Blueprints/BP_Player_Medic 如果存在
bp2_path = "/Game/GGBOM/Blueprints/BP_Player_Medic"
if unreal.EditorAssetLibrary.does_asset_exist(bp2_path):
    bp2 = unreal.load_asset(bp2_path)
    out_lines.append(f"=== BLUEPRINT 2: {bp2.get_path_name()} ===")
    scs2 = bp2.simple_construction_script
    if scs2:
        for node in scs2.get_all_nodes():
            out_lines.append(f"  SCS Node: {node.get_variable_name()} ({node.component_class.get_name()})")

with open("/Users/cc/Desktop/GGBOM/xxxx/Content/Python/bp_scs_inspect.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))

print("Inspection completed.")
