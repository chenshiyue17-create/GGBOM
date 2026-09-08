#!/usr/bin/env python3
"""Retired phase builder. Historical archive scripts cannot validate the current game."""
import json


def main():
    print(json.dumps({"status": "BLOCKED", "runtime_status": "NOT_RUN",
                      "reason": "P03/P04/P05 builders are archived. Use tools/dev.py test and validate; migrate live assets under a scoped change plan."}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
