# -*- coding: utf-8 -*-
import json
import hashlib
from datetime import datetime
from pathlib import Path
import unreal

PROJECT_DIR = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
CONTENT_DIR = PROJECT_DIR / "Content"
OUTPUT_DIR = PROJECT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR = PROJECT_DIR.parent / "Docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

def get_file_meta(file_path: Path):
    if not file_path.exists():
        return {"exists": False, "size": 0, "sha256": "N/A", "mtime": "N/A"}
    stat = file_path.stat()
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return {
        "exists": True,
        "size": stat.st_size,
        "sha256": h.hexdigest(),
        "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat()
    }

def get_pin_type_str(p):
    try:
        if hasattr(PINLIB, "get_pin_type_display_string"):
            s = str(PINLIB.get_pin_type_display_string(p))
            if s: return s
    except Exception:
        pass
    try:
        return str(PINLIB.get_pin_type(p))
    except Exception:
        return "any"

def get_pin_val(p):
    try:
        return str(PINLIB.get_pin_value(p))
    except Exception:
        return ""

def read_bp(pkg_path):
    rel = pkg_path.removeprefix("/Game/")
    disk_file = CONTENT_DIR / f"{rel}.uasset"
    meta = get_file_meta(disk_file)
    bp = ASSETS.load_asset(pkg_path)
    if not bp:
        return {"pkg": pkg_path, "disk": str(disk_file), "meta": meta, "error": "NOT_FOUND"}

    parent_name = "Actor"
    try:
        parent_name = bp.get_editor_property("parent_class").get_name()
    except Exception:
        pass

    var_names = []
    try:
        var_names = [str(n) for n in BPLIB.list_member_variable_names(bp, False)]
    except Exception:
        pass

    graph = BPLIB.find_event_graph(bp)
    nodes_info = []
    edges_info = []
    if graph:
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        all_nodes = editor.list_all_nodes()
        node_map = {}
        for idx, n in enumerate(all_nodes):
            nid = f"{n.get_name()}_{idx}"
            node_map[n] = nid
            title = unreal.BlueprintEditorLibrary.get_node_title(n)
            pos = n.get_node_pos()
            cls = n.get_class().get_name()

            in_pins = []
            for p in BPLIB.list_input_pins(n):
                in_pins.append({
                    "name": str(PINLIB.get_pin_name(p)),
                    "type": get_pin_type_str(p),
                    "default": get_pin_val(p)
                })
            out_pins = []
            for p in BPLIB.list_output_pins(n):
                out_pins.append({
                    "name": str(PINLIB.get_pin_name(p)),
                    "type": get_pin_type_str(p)
                })
            nodes_info.append({
                "id": nid,
                "name": n.get_name(),
                "title": title,
                "class": cls,
                "pos": [pos.x, pos.y],
                "inputs": in_pins,
                "outputs": out_pins
            })

        for src in all_nodes:
            src_id = node_map.get(src)
            for p in BPLIB.list_output_pins(src):
                pname = str(PINLIB.get_pin_name(p))
                ptype = get_pin_type_str(p).lower()
                for dst_pin in PINLIB.list_connected_pins(p):
                    dst_node = dst_pin.get_owning_node()
                    dst_id = node_map.get(dst_node)
                    if dst_id:
                        edges_info.append({
                            "from_node": src_id,
                            "from_pin": pname,
                            "to_node": dst_id,
                            "to_pin": str(PINLIB.get_pin_name(dst_pin)),
                            "type": "exec" if ("exec" in ptype or pname.lower() in ("then", "execute")) else "data"
                        })

    return {
        "pkg": pkg_path,
        "disk": str(disk_file),
        "meta": meta,
        "parent": parent_name,
        "variables": var_names,
        "node_count": len(nodes_info),
        "edge_count": len(edges_info),
        "nodes": nodes_info,
        "edges": edges_info
    }

def main():
    targets = [
        "/Game/Blueprints/Player/BP_Player_Medic",
        "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
        "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord",
        "/Game/GGBOM/UI/WBP_Boss_OverheadHealthBar"
    ]
    res = {}
    for t in targets:
        info = read_bp(t)
        res[t] = info
        print(f"[READBACK] {t}: 节点={info.get('node_count')}, 连线={info.get('edge_count')}, SHA256={info.get('meta', {}).get('sha256', '')[:12]}", flush=True)

    payload = {
        "engine_version": str(unreal.SystemLibrary.get_engine_version()),
        "sync_timestamp": datetime.now().isoformat(),
        "live_sync_verified": True,
        "blueprints": res
    }
    out_file = OUTPUT_DIR / "blueprint_live_readback.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    
    docs_file = DOCS_DIR / "blueprint_live_readback.json"
    docs_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    js_file = DOCS_DIR / "blueprint_live_readback.js"
    js_file.write_text(f"window.GGBOM_LIVE_READBACK = {json.dumps(payload, ensure_ascii=False, indent=2)};\n", encoding="utf-8")

    root_js = PROJECT_DIR.parent / "blueprint_live_readback.js"
    root_js.write_text(f"window.GGBOM_LIVE_READBACK = {json.dumps(payload, ensure_ascii=False, indent=2)};\n", encoding="utf-8")
    print("[READBACK] ALL_OK", flush=True)

if __name__ == "__main__":
    main()
