# -*- coding: utf-8 -*-
import unreal
import sys

log = lambda m: (print(f"[ZombieTest] {m}"), sys.stdout.flush())

BPLIB = unreal.BlueprintEditorLibrary
ASSETS = unreal.EditorAssetLibrary

PATH = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
log(f"1. Loading existing {PATH}...")
bp = unreal.load_asset(PATH)

log("2. Re-creating clean blueprint to eliminate dangling graph pointers...")
ASSETS.delete_asset(PATH)
bp = BPLIB.create_blueprint_asset_with_parent(PATH, unreal.Actor.static_class())
if not bp:
    log("Failed to create blueprint!")
    sys.exit(1)

log("3. Getting graph editor...")
graph = BPLIB.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

log("4. Testing add_call_function_node on clean graph...")
node = ed.add_call_function_node("/Script/Engine.Actor.K2_AddActorWorldOffset")
log(f"Successfully created node: {node.get_path_name()}!")

BPLIB.compile_blueprint(bp)
ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
log("5. Compiled and saved successfully!")
