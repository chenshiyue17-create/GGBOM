"""Atomic single-file writes and recoverable multi-file configuration transactions."""
import base64
from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path, value):
    atomic_bytes(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8"))


def row_index(rows):
    if isinstance(rows, dict):
        return rows
    if not isinstance(rows, list):
        raise ValueError("Data rows must be a dictionary or list")
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("Name"), str) or not row["Name"]:
            raise ValueError("Every list row needs a non-empty Name")
        if row["Name"] in result:
            raise ValueError(f"Duplicate row Name: {row['Name']}")
        result[row["Name"]] = row
    return result


def diff_rows(old_rows, new_rows):
    old, new = row_index(old_rows), row_index(new_rows)
    modified = sorted(key for key in old.keys() & new.keys() if old[key] != new[key])
    return {"added": sorted(new.keys() - old.keys()), "removed": sorted(old.keys() - new.keys()),
            "modified": modified, "changes": {key: {"old": old[key], "new": new[key]} for key in modified},
            "totalOld": len(old), "totalNew": len(new)}


@contextmanager
def config_lock(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / ".ggbom-write.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise RuntimeError(f"Configuration writer is locked: {lock}. If its process crashed, close all writers and remove this stale lock before recovery.")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)


def _valid_name(name):
    if not isinstance(name, str) or Path(name).name != name or "/" in name or "\\" in name or not name.endswith(".json"):
        raise ValueError(f"Invalid configuration filename: {name!r}")


def _recover(directory):
    journal = directory / ".ggbom-transaction.json"
    if not journal.exists():
        return
    original = json.loads(journal.read_text(encoding="utf-8"))
    for name, encoded in original.items():
        _valid_name(name)
        if encoded is None:
            (directory / name).unlink(missing_ok=True)
        else:
            atomic_bytes(directory / name, base64.b64decode(encoded, validate=True))
    journal.unlink()


def recover_pending(directory):
    directory = Path(directory)
    with config_lock(directory):
        _recover(directory)


def commit_json_files(directory, updates, validate_current=None):
    """Recoverable transaction for cooperating writers. External readers must not read mid-commit."""
    directory = Path(directory)
    if not updates:
        raise ValueError("No configuration changes supplied")
    encoded = {}
    for name, value in updates.items():
        _valid_name(name)
        encoded[name] = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
    with config_lock(directory):
        _recover(directory)
        if validate_current is not None:
            validate_current()
        old = {name: base64.b64encode((directory / name).read_bytes()).decode("ascii")
               if (directory / name).exists() else None for name in encoded}
        journal = directory / ".ggbom-transaction.json"
        atomic_json(journal, old)
        try:
            for name, value in encoded.items():
                atomic_bytes(directory / name, value)
            journal.unlink()  # Commit point. Before this, startup recovery rolls back all tables.
        except BaseException:
            _recover(directory)
            raise
