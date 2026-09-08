"""Retired global rebuild entry. Use tools/dev.py apply-enemy-defaults for numeric config.

The old implementation reset camera-independent combat art/physics and removed
nodes, then inferred ALL_PASS from asset saving. It is available in Git history,
not automatically invoked by the supported developer workflow.
"""


def execute_master_combat_closure():
    raise RuntimeError("BLOCKED: global combat rebuild is retired. Use tools/dev.py config-plan; gameplay graph migration requires live UE validation.")


if __name__ == "__main__":
    execute_master_combat_closure()
