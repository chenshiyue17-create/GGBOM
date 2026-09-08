#!/usr/bin/env python3
"""Launch the generated Blueprint game in a portrait UE window."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_EDITOR = Path("/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd")


def main() -> int:
    editor = Path(os.environ.get("UE5_EDITOR", str(DEFAULT_EDITOR)))
    if not editor.is_file():
        raise SystemExit(f"UE5_EDITOR 不存在: {editor}")
    command = [
        str(editor), str(ROOT / "xxxx.uproject"),
        "/Game/GGBOM/Maps/MAP_GGBOM_Main", "-game", "-windowed",
        "-ResX=562", "-ResY=1000", "-log",
    ]
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
