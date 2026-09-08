# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/probe_wbp_combat_hud.txt"

w_path = "/Game/GGBOM/UI/WBP_GGBOM_CombatHUD"
bp = unreal.EditorAssetLibrary.load_asset(w_path)
lines = [f"WBP Combat HUD: {bp.get_name() if bp else 'None'}"]

if bp:
    cdo = unreal.get_default_object(bp.generated_class())
    lines.append(f"CDO: {cdo.get_name() if cdo else 'None'}")
    if hasattr(bp, "widget_tree"):
        root = bp.widget_tree.root_widget
        lines.append(f"RootWidget: {root.get_name() if root else 'None'}")
        def dump_w(w, depth=0):
            indent = "  " * depth
            lines.append(f"{indent}- [{w.get_class().get_name()}] {w.get_name()}")
            if hasattr(w, "get_all_children"):
                for child in w.get_all_children():
                    dump_w(child, depth + 1)
        if root:
            dump_w(root)

OUT.write_text("\n".join(lines), encoding="utf-8")
print("PROBE_WBP_DONE")
