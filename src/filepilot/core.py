"""Core file scanning, planning, organizing, and undo operations."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from .history import (
    MoveRecord,
    Operation,
    ensure_history_available,
    pop_last_operation,
    save_operation,
)
from .names import dated_filename, unique_path
from .rules import CATEGORY_ORDER, category_counts, detect_category


@dataclass(frozen=True)
class ScanResult:
    folder: Path
    files: list[Path]
    counts: dict[str, int]


@dataclass(frozen=True)
class PlannedMove:
    source: Path
    destination: Path
    category: str


def iter_files(folder: Path) -> list[Path]:
    """Return direct child files only, keeping organize operations predictable."""
    return sorted(path for path in folder.iterdir() if path.is_file())


def scan_folder(folder: Path) -> ScanResult:
    files = iter_files(folder)
    counts = category_counts(files)
    return ScanResult(
        folder=folder,
        files=files,
        counts={category: counts[category] for category in CATEGORY_ORDER},
    )


def plan_organize(folder: Path) -> list[PlannedMove]:
    files = iter_files(folder)
    planned: list[PlannedMove] = []
    reserved: set[Path] = set()

    for file in files:
        category = detect_category(file)
        date_prefix = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d")
        destination_dir = folder / category
        destination = destination_dir / dated_filename(file, date_prefix)
        safe_destination = unique_path(destination, reserved)
        reserved.add(safe_destination)
        planned.append(
            PlannedMove(source=file, destination=safe_destination, category=category)
        )

    return planned


def organize_folder(
    folder: Path,
    progress_callback: Callable[[PlannedMove], None] | None = None,
) -> tuple[list[PlannedMove], Operation | None]:
    planned = plan_organize(folder)
    if planned:
        ensure_history_available()

    completed: list[MoveRecord] = []

    for move in planned:
        move.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(move.source, move.destination)
        if progress_callback is not None:
            progress_callback(move)
        completed.append(
            MoveRecord(
                original=str(move.source.resolve()),
                organized=str(move.destination.resolve()),
            )
        )

    operation = save_operation(folder, completed) if completed else None
    return planned, operation


def undo_last_operation(
    progress_callback: Callable[[MoveRecord, MoveRecord | None], None] | None = None,
) -> tuple[Operation | None, list[MoveRecord]]:
    operation = pop_last_operation()
    if operation is None:
        return None, []

    restored: list[MoveRecord] = []
    for move in reversed(operation.moves):
        organized = Path(move.organized)
        original = Path(move.original)

        if not organized.exists():
            if progress_callback is not None:
                progress_callback(move, None)
            continue

        original.parent.mkdir(parents=True, exist_ok=True)
        safe_original = unique_path(original)
        shutil.move(organized, safe_original)
        restored_move = MoveRecord(original=str(safe_original), organized=str(organized))
        restored.append(restored_move)
        if progress_callback is not None:
            progress_callback(move, restored_move)

    return operation, restored
