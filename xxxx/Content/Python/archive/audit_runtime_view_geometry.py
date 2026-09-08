# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import unreal


PROJECT_ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
REPORT_PATH = PROJECT_ROOT / "output" / "runtime_view_geometry_audit.json"


def vec(v):
    return [float(v.x), float(v.y), float(v.z)]


def rot(r):
    return [float(r.pitch), float(r.yaw), float(r.roll)]


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def rel_rot(comp):
    r = prop(comp, "relative_rotation")
    if r is not None:
        return rot(r)
    try:
        return rot(comp.get_editor_property("relative_rotation"))
    except Exception:
        return None


def rel_loc(comp):
    v = prop(comp, "relative_location")
    if v is not None:
        return vec(v)
    try:
        return vec(comp.get_editor_property("relative_location"))
    except Exception:
        return None


def safe_label(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def main():
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    rows = []
    for actor in actors:
        label = safe_label(actor)
        item = {
            "label": label,
            "class": actor.get_class().get_name(),
            "location": vec(actor.get_actor_location()),
            "rotation": rot(actor.get_actor_rotation()),
            "scale": vec(actor.get_actor_scale3d()),
        }
        cam = actor.get_component_by_class(unreal.CameraComponent)
        if cam:
            item["camera"] = {
                "projection_mode": str(prop(cam, "projection_mode")),
                "ortho_width": prop(cam, "ortho_width"),
                "aspect_ratio": prop(cam, "aspect_ratio"),
                "constrain_aspect_ratio": prop(cam, "constrain_aspect_ratio", prop(cam, "b_constrain_aspect_ratio")),
            }
        spr = actor.get_component_by_class(unreal.PaperSpriteComponent)
        if spr:
            sprite = prop(spr, "source_sprite")
            bounds = None
            try:
                b = spr.bounds
                bounds = {"origin": vec(b.origin), "box_extent": vec(b.box_extent), "sphere_radius": float(b.sphere_radius)}
            except Exception:
                pass
            item["sprite_component"] = {
                "relative_rotation": rel_rot(spr),
                "relative_location": rel_loc(spr),
                "source_sprite": sprite.get_path_name() if sprite else None,
                "visible": prop(spr, "visible"),
                "hidden_in_game": prop(spr, "hidden_in_game"),
                "bounds": bounds,
            }
        rows.append(item)
    REPORT_PATH.write_text(json.dumps({"time": datetime.now().isoformat(timespec="seconds"), "map": MAP_PATH, "actors": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    unreal.log(f"[GGBOM-ViewAudit] wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
