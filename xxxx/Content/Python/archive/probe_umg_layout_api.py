# -*- coding: utf-8 -*-
import unreal

bp_path = "/Game/GGBOM/UI/WBP_GGBOM_CombatHUD"
widget_bp = unreal.load_asset(bp_path)
if not widget_bp:
    factory = unreal.WidgetBlueprintFactory()
    widget_bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset("WBP_GGBOM_CombatHUD", "/Game/GGBOM/UI", unreal.WidgetBlueprint, factory)

tree = widget_bp.get_editor_property("widget_tree")
print("Tree:", tree)
root = tree.get_editor_property("root_widget")
if not root:
    root = tree.construct_widget(unreal.CanvasPanel)
    tree.set_editor_property("root_widget", root)

img = tree.construct_widget(unreal.Image)
slot = root.add_child_to_canvas(img)

print("Slot layout data:", slot.get_editor_property("layout_data"))
layout = slot.get_editor_property("layout_data")
print("Anchors:", dir(layout.anchors))
print("Offsets:", dir(layout.offsets))

unreal.BlueprintEditorLibrary.compile_blueprint(widget_bp)
unreal.EditorAssetLibrary.save_loaded_asset(widget_bp, only_if_is_dirty=False)
print("Widget compiled successfully!")
