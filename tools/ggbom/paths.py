"""Machine-local paths; never commit a developer's engine installation path."""
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "xxxx"
DATA_DIR = PROJECT_ROOT / "Content" / "Data"
REPORT_DIR = PROJECT_ROOT / "Saved" / "GGBOM"


def local_settings():
    path = REPO_ROOT / ".ggbom.local.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(".ggbom.local.json must be an object")
    return data


def engine_binary(commandlet=False):
    settings = local_settings()
    explicit = os.environ.get("GGBOM_UE_BIN") or settings.get("ue_bin")
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_file():
            return path.resolve()
        raise FileNotFoundError(f"UE executable does not exist: {path}")
    root = os.environ.get("GGBOM_UE_ROOT") or settings.get("engine_root")
    if not root:
        raise FileNotFoundError("Set GGBOM_UE_ROOT or engine_root in .ggbom.local.json on this machine")
    root = Path(root).expanduser()
    if root.name != "Engine":
        root /= "Engine"
    names = (["Binaries/Win64/UnrealEditor-Cmd.exe", "Binaries/Mac/UnrealEditor-Cmd",
              "Binaries/Linux/UnrealEditor-Cmd"] if commandlet else [])
    names += ["Binaries/Win64/UnrealEditor.exe",
              "Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor",
              "Binaries/Mac/UnrealEditor", "Binaries/Linux/UnrealEditor"]
    for name in names:
        path = root / name
        if path.is_file():
            return path.resolve()
    raise FileNotFoundError(f"No UnrealEditor executable under {root}")
