# -*- coding: utf-8 -*-
"""
probe_and_hide_umg_bossbar.py
检查 WBP_GGBOM_CombatHUD 中的控件树，将旧的 TopBossHeader / BossHealthBar 设为 Collapsed / Hidden，
确保用户指定的 4 大素材构成的豪华 Boss 血条无遮挡、零干扰地居中呈现。
"""
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/probe_and_hide_umg_bossbar.txt"

w_path = "/Game/GGBOM/UI/WBP_GGBOM_CombatHUD"
bp = unreal.EditorAssetLibrary.load_asset(w_path)
lines = []

if not bp:
    lines.append(f"Widget not found: {w_path}")
else:
    lines.append(f"Loaded: {w_path}")
    tree = bp.get_editor_property("widget_tree") if hasattr(bp, "widget_tree") else None
    if tree:
        all_widgets = tree.get_editor_property("all_widgets") if hasattr(tree, "all_widgets") else []
        lines.append(f"Total widgets: {len(all_widgets)}")
        for w in all_widgets:
            name = w.get_name()
            cls_name = w.get_class().get_name()
            lines.append(f"  Widget: {name} ({cls_name})")
            # 如果是旧 BossBar 相关控件，直接将其设为 Collapsed
            if any(k in name.lower() for k in ["boss", "header", "topboss"]):
                try:
                    w.set_editor_property("visibility", unreal.SlateVisibility.COLLAPSED)
                    lines.append(f"    -> Set {name} to SlateVisibility.COLLAPSED")
                except Exception as e:
                    lines.append(f"    -> Error setting visibility on {name}: {e}")
        
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        saved = unreal.EditorAssetLibrary.save_loaded_asset(bp)
        lines.append(f"Blueprint saved: {saved}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
