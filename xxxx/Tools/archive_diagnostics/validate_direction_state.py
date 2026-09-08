#!/usr/bin/env python3
"""Validate the persisted Blueprint direction topology from the UE audit report."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "output" / "direction_graph_after_fix.json"
OUT = ROOT / "output" / "direction_state_validation.json"


def graph(asset: dict, name: str) -> dict:
    return next(item for item in asset["graphs"] if item["name"] == name)


def node(item_graph: dict, title: str) -> dict:
    return next(item for item in item_graph["nodes"] if item["title"] == title)


def linked_titles(item_graph: dict, item_node: dict, pin_name: str, output: bool) -> set[str]:
    pin_group = item_node["outputs" if output else "inputs"]
    item_pin = next(pin for pin in pin_group if pin["name"] == pin_name)
    titles = {item["name"]: item["title"] for item in item_graph["nodes"]}
    return {titles[name] for name in item_pin["linked_nodes"]}


def pin_value(item_node: dict, pin_name: str) -> str:
    return next(pin for pin in item_node["inputs"] if pin["name"] == pin_name)["value"]


def main() -> int:
    payload = json.loads(AUDIT.read_text(encoding="utf-8"))
    player = payload["player"]
    projectile = payload["projectile"]
    checks: dict[str, bool] = {}

    required_player_vars = {"MoveInput", "FacingDirection", "ShotDirection"}
    checks["three_independent_player_variables"] = required_player_vars.issubset(player["variables"])
    checks["player_has_no_graph_errors"] = not player["compiler_errors"]
    checks["projectile_has_no_graph_errors"] = not projectile["compiler_errors"]
    checks["event_graph_is_canonical_size"] = player["node_count"] <= 20

    event_graph = graph(player, "EventGraph")
    tick = next(item for item in event_graph["nodes"] if item["class"] == "K2Node_Event" and "Tick" in item["title"])
    checks["single_tick_flow"] = len(linked_titles(event_graph, tick, "then", True)) == 1
    checks["movement_reads_only_move_input"] = (
        "Add Actor World Offset" in linked_titles(event_graph, node(event_graph, "Get MoveInput"), "MoveInput", True)
    )
    sample_graph = graph(player, "SampleMoveInput")
    move_steps = {
        float(pin_value(item, "A"))
        for item in sample_graph["nodes"]
        if item["title"] == "SelectFloat"
    }
    checks["movement_step_is_fast_30fps"] = move_steps == {-7.5, 7.5}
    sample_nodes = {item["name"]: item for item in sample_graph["nodes"]}
    key_steps = {}
    for key_node in (item for item in sample_graph["nodes"] if item["title"] == "IsInputKeyDown"):
        key_name = pin_value(key_node, "Key")
        linked_select = next(pin for pin in key_node["outputs"] if pin["name"] == "ReturnValue")["linked_nodes"][0]
        key_steps[key_name] = float(pin_value(sample_nodes[linked_select], "A"))
    checks["wasd_world_mapping_is_correct"] = key_steps == {"A": 7.5, "D": -7.5, "W": 7.5, "S": -7.5}

    scale_graph = graph(player, "UpdateFacingScale")
    scale_select = node(scale_graph, "SelectFloat")
    checks["horizontal_flip_matches_world_mapping"] = (
        float(pin_value(scale_select, "A")) == -0.45
        and float(pin_value(scale_select, "B")) == 0.45
    )

    facing_graph = graph(player, "UpdateFacingDirection")
    checks["facing_retains_last_nonzero_move"] = (
        linked_titles(facing_graph, node(facing_graph, "Get MoveInput"), "MoveInput", True)
        == {"Vector_IsNearlyZero", "SelectVector"}
        and linked_titles(facing_graph, node(facing_graph, "Get FacingDirection"), "FacingDirection", True)
        == {"SelectVector"}
        and linked_titles(facing_graph, node(facing_graph, "SelectVector"), "ReturnValue", True)
        == {"Set FacingDirection"}
    )

    fire_graph = graph(player, "TryFireProjectile")
    checks["shot_is_facing_snapshot"] = (
        linked_titles(fire_graph, node(fire_graph, "Get FacingDirection"), "FacingDirection", True)
        == {"Set ShotDirection"}
        and linked_titles(fire_graph, node(fire_graph, "Set ShotDirection"), "then", True)
        == {"SpawnDirectionalProjectile"}
    )

    spawn_graph = graph(player, "SpawnDirectionalProjectile")
    shot_targets = linked_titles(spawn_graph, node(spawn_graph, "Get ShotDirection"), "ShotDirection", True)
    checks["spawn_rotation_uses_shot_direction"] = "MakeRotFromX" in shot_targets
    vector_add_nodes = [item for item in spawn_graph["nodes"] if item["title"] == "vector + vector"]
    checks["muzzle_is_above_player_feet"] = any("55" in pin_value(item, "B") for item in vector_add_nodes)

    projectile_graph = graph(projectile, "EventGraph")
    checks["projectile_captures_spawn_forward_once"] = (
        linked_titles(projectile_graph, node(projectile_graph, "GetActorForwardVector"), "ReturnValue", True)
        == {"Set ShotDirection"}
    )
    checks["projectile_flight_reads_own_shot_direction"] = (
        "Normalize" in linked_titles(projectile_graph, node(projectile_graph, "Get ShotDirection"), "ShotDirection", True)
    )

    result = {
        "DIRECTION_STATE_VALIDATION": "PASS" if all(checks.values()) else "FAIL",
        "source": str(AUDIT),
        "checks": checks,
        "summary": {
            "player_event_nodes": player["node_count"],
            "player_variables": player["variables"],
            "projectile_event_nodes": projectile["node_count"],
            "projectile_variables": projectile["variables"],
        },
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"DIRECTION_STATE_VALIDATION={result['DIRECTION_STATE_VALIDATION']}")
    return 0 if result["DIRECTION_STATE_VALIDATION"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
