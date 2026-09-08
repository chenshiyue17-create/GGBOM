"""Existing numeric CDO defaults only. Does not create assets, modify graphs or place actors."""
import math


def apply_enemy_defaults(unreal, plan):
    changes, originals, saved = [], [], []
    # Complete preflight before the first mutation.
    for binding in plan["bindings"]:
        asset = unreal.load_asset(binding["asset_path"])
        cls = unreal.load_class(None, binding["class_path"])
        if asset is None or cls is None:
            raise RuntimeError(f"Required existing class/asset is missing: {binding['class_path']}")
        cdo = unreal.get_default_object(cls)
        if cdo is None:
            raise RuntimeError(f"Missing CDO: {binding['class_path']}")
        props = dict(binding["properties"])
        props["CurrentHealth"] = props["MaxHealth"]
        previous = {}
        for key, value in props.items():
            old = cdo.get_editor_property(key)  # Unknown fields fail before any write.
            if type(old) not in (int, float) or not math.isfinite(old):
                raise RuntimeError(f"Not a finite numeric property: {binding['class_path']}.{key}")
            previous[key] = old
        changes.append((binding, asset, cdo, props))
        originals.append((asset, cdo, previous))
    try:
        for binding, asset, cdo, props in changes:
            for key, value in props.items():
                cdo.set_editor_property(key, value)
            for key, value in props.items():
                actual = cdo.get_editor_property(key)
                if not math.isclose(actual, value, rel_tol=1e-6, abs_tol=1e-6):
                    raise RuntimeError(f"Readback mismatch: {binding['row_id']}.{key}: {actual} != {value}")
            if not unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False):
                raise RuntimeError(f"Save failed: {binding['asset_path']}")
            saved.append({"row_id": binding["row_id"], "asset_path": binding["asset_path"],
                          "editor_readback": {key: cdo.get_editor_property(key) for key in props}})
    except Exception as error:
        rollback_errors = []
        for asset, cdo, props in originals:
            try:
                for key, value in props.items():
                    cdo.set_editor_property(key, value)
                if not unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False):
                    raise RuntimeError("restore save failed")
            except Exception as rollback_error:
                rollback_errors.append(str(rollback_error))
        raise RuntimeError(f"Apply failed: {error}; rollback_errors={rollback_errors}") from error
    return {**plan, "status": "APPLIED_EDITOR_DEFAULTS", "saved": saved,
            "runtime_status": "NOT_RUN", "disk_reload_status": "NOT_RUN"}
