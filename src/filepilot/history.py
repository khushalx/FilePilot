"""JSON history storage for undo support."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def get_app_dir() -> Path:
    """Return FilePilot's history directory.

    The default intentionally uses Path.home() so it works across Windows,
    macOS, and Linux. FILEPILOT_HOME is only an override for tests, CI, or
    users who want history somewhere else.
    """
    configured_home = os.environ.get("FILEPILOT_HOME")
    if configured_home:
        return Path(configured_home).expanduser()
    return Path.home() / ".filepilot"


def get_history_file() -> Path:
    return get_app_dir() / "history.json"


@dataclass(frozen=True)
class MoveRecord:
    original: str
    organized: str


@dataclass(frozen=True)
class Operation:
    id: str
    folder: str
    created_at: str
    moves: list[MoveRecord]


def _read_history() -> list[dict[str, Any]]:
    history_file = get_history_file()
    if not history_file.exists():
        return []

    try:
        data = json.loads(history_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if isinstance(data, list):
        return data
    return []


def _write_history(history: list[dict[str, Any]]) -> None:
    app_dir = get_app_dir()
    app_dir.mkdir(parents=True, exist_ok=True)
    get_history_file().write_text(json.dumps(history, indent=2), encoding="utf-8")


def ensure_history_available() -> None:
    """Fail before moving files if undo history cannot be written."""
    app_dir = get_app_dir()
    history_file = get_history_file()
    app_dir.mkdir(parents=True, exist_ok=True)
    if history_file.exists():
        _read_history()
    else:
        history_file.write_text("[]", encoding="utf-8")


def save_operation(folder: Path, moves: list[MoveRecord]) -> Operation:
    created_at = datetime.now(timezone.utc).isoformat()
    operation = Operation(
        id=created_at.replace(":", "").replace("+", "Z"),
        folder=str(folder.resolve()),
        created_at=created_at,
        moves=moves,
    )

    history = _read_history()
    history.append(asdict(operation))
    _write_history(history)
    return operation


def pop_last_operation() -> Operation | None:
    history = _read_history()
    if not history:
        return None

    raw_operation = history.pop()
    _write_history(history)

    moves = [
        MoveRecord(original=move["original"], organized=move["organized"])
        for move in raw_operation.get("moves", [])
    ]
    return Operation(
        id=raw_operation.get("id", ""),
        folder=raw_operation.get("folder", ""),
        created_at=raw_operation.get("created_at", ""),
        moves=moves,
    )
