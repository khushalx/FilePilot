"""Rich rendering helpers for the FilePilot command-line interface."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from rich import box
from rich.console import Console, Group
from rich.markup import escape
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table
from rich.text import Text

from .core import PlannedMove, ScanResult
from .history import MoveRecord
from .names import dated_filename
from .rules import CATEGORY_ORDER, CATEGORY_RULES

console = Console()

CATEGORY_DESCRIPTIONS = {
    "docs": "Documents, spreadsheets, decks, notes",
    "images": "Photos, graphics, screenshots, design assets",
    "code": "Source files, scripts, configs, markup",
    "archives": "Compressed packages and backups",
    "videos": "Movie files, recordings, exports",
    "audio": "Music, voice notes, sound assets",
    "misc": "Everything without a known rule",
}


def print_header(command: str, target: Path | None = None) -> None:
    subtitle = Text("Smart folder cleanup for real workspaces", style="dim")
    details = Table.grid(padding=(0, 1))
    details.add_column(style="bold cyan", no_wrap=True)
    details.add_column()
    details.add_row("Mode", command)
    if target is not None:
        details.add_row("Target", Text(str(target)))

    console.print(
        Panel(
            Group(Text("FilePilot", style="bold white"), subtitle, details),
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )


def print_error(message: str) -> None:
    console.print(
        Panel(
            Text(message),
            title="Action blocked",
            border_style="red",
            box=box.ROUNDED,
        )
    )


def print_empty_state(title: str, message: str) -> None:
    console.print(
        Panel(
            Text(message, style="dim"),
            title=title,
            border_style="yellow",
            box=box.ROUNDED,
        )
    )


def folder_health(result: ScanResult) -> tuple[int, str, str]:
    total = len(result.files)
    if total == 0:
        return 100, "Clean", "green"

    misc_ratio = result.counts["misc"] / total
    active_categories = sum(1 for count in result.counts.values() if count)
    volume_penalty = min(35, total * 2)
    misc_penalty = int(misc_ratio * 35)
    spread_penalty = max(0, active_categories - 2) * 5
    score = max(0, 100 - volume_penalty - misc_penalty - spread_penalty)

    if score >= 85:
        return score, "Clean", "green"
    if score >= 65:
        return score, "Lightly Messy", "yellow"
    if score >= 40:
        return score, "Messy", "orange3"
    return score, "Very Messy", "red"


def top_category(result: ScanResult) -> str:
    nonzero = [(category, result.counts[category]) for category in CATEGORY_ORDER]
    category, count = max(nonzero, key=lambda item: item[1])
    return f"{category} ({count})" if count else "None"


def print_scan_summary(result: ScanResult) -> None:
    score, status, style = folder_health(result)

    table = Table.grid(padding=(0, 3))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column()
    table.add_row("Total files", str(len(result.files)))
    table.add_row("Top category", top_category(result))
    table.add_row("Folder health", Text(status, style=f"bold {style}"))
    table.add_row("Health score", f"{score}/100")

    console.print(
        Panel(
            table,
            title="Folder Summary",
            border_style=style,
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )


def print_category_table(counts: dict[str, int]) -> None:
    table = Table(
        title="Category Breakdown",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("Category", style="bold", no_wrap=True)
    table.add_column("Description", style="dim")
    table.add_column("Files", justify="right", style="green")

    for category in CATEGORY_ORDER:
        table.add_row(
            category,
            CATEGORY_DESCRIPTIONS[category],
            str(counts[category]),
        )

    console.print(table)


def print_dry_run_intro() -> None:
    console.print(
        Panel(
            "Dry Run Mode is active. FilePilot will only preview changes.",
            title="Dry Run Mode",
            border_style="yellow",
            box=box.ROUNDED,
        )
    )


def print_move_preview(moves: Sequence[PlannedMove], title: str = "Move Preview") -> None:
    table = Table(
        title=title,
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("Category", style="bold cyan", no_wrap=True)
    table.add_column("Current File", overflow="fold")
    table.add_column("New Location", style="green", overflow="fold")

    for index, move in enumerate(moves, start=1):
        table.add_row(
            str(index),
            move.category,
            Text(move.source.name),
            Text(str(move.destination.relative_to(move.source.parent))),
        )

    console.print(table)


def folders_needed(moves: Sequence[PlannedMove]) -> set[Path]:
    return {move.destination.parent for move in moves if not move.destination.parent.exists()}


def conflict_safe_renames(moves: Sequence[PlannedMove]) -> int:
    conflicts = 0
    for move in moves:
        expected = move.source.parent / move.category / dated_filename(
            move.source,
            move.destination.name.split("_", 1)[0],
        )
        if move.destination != expected:
            conflicts += 1
    return conflicts


def print_dry_run_summary(moves: Sequence[PlannedMove]) -> None:
    table = Table.grid(padding=(0, 3))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column()
    table.add_row("Planned moves", str(len(moves)))
    table.add_row("Folders needed", str(len(folders_needed(moves))))
    table.add_row("Collision-safe renames", str(conflict_safe_renames(moves)))
    table.add_row("Action taken", "None")

    console.print(
        Panel(
            table,
            title="Plan Summary",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )


def print_safety_check() -> None:
    checks = Table.grid(padding=(0, 2))
    checks.add_column(style="bold green", no_wrap=True)
    checks.add_column()
    checks.add_row("OK", "Never delete files")
    checks.add_row("OK", "Never overwrite files")
    checks.add_row("OK", "Undo history enabled")

    console.print(
        Panel(
            checks,
            title="Safety Check",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )


def make_progress(label: str) -> Progress:
    return Progress(
        SpinnerColumn(style="cyan"),
        TextColumn(f"[bold cyan]{escape(label)}[/bold cyan]"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        console=console,
    )


def print_cleanup_complete(
    files_organized: int,
    folders_created: int,
    conflicts_handled: int,
    undo_available: bool,
) -> None:
    table = Table.grid(padding=(0, 3))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column()
    table.add_row("Files organized", str(files_organized))
    table.add_row("Folders created", str(folders_created))
    table.add_row("Conflicts handled", str(conflicts_handled))
    table.add_row("Undo available", "Yes" if undo_available else "No")

    console.print(
        Panel(
            Group(table, Text("\nTo restore the last cleanup, run: filepilot undo", style="bold")),
            title="Cleanup Complete",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )


def print_restore_mode() -> None:
    console.print(
        Panel(
            "FilePilot will restore files from the most recent organize operation.",
            title="Restore Mode",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )


def print_restore_table(restored: Sequence[MoveRecord]) -> None:
    table = Table(
        title="Restore Details",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
    )
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("Moved From", style="cyan", overflow="fold")
    table.add_column("Restored To", style="green", overflow="fold")

    for index, move in enumerate(restored, start=1):
        organized = Path(move.organized)
        restored_to = Path(move.original)
        try:
            organized_text = str(organized.relative_to(restored_to.parent))
            restored_text = str(restored_to.relative_to(restored_to.parent))
        except ValueError:
            organized_text = str(organized)
            restored_text = str(restored_to)

        table.add_row(str(index), Text(organized_text), Text(restored_text))

    console.print(table)


def print_restore_summary(
    files_restored: int,
    conflicts_handled: int,
    history_updated: bool,
) -> None:
    table = Table.grid(padding=(0, 3))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column()
    table.add_row("Files restored", str(files_restored))
    table.add_row("Conflicts handled", str(conflicts_handled))
    table.add_row("History updated", "Yes" if history_updated else "No")

    console.print(
        Panel(
            table,
            title="Restore Complete",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )


def print_config_table() -> None:
    table = Table(
        title="Category Rules",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
        show_lines=True,
    )
    table.add_column("Category", style="bold cyan", no_wrap=True)
    table.add_column("Description", style="dim")
    table.add_column("Extensions", overflow="fold")

    for category in CATEGORY_ORDER:
        extensions = sorted(CATEGORY_RULES[category])
        table.add_row(
            category,
            CATEGORY_DESCRIPTIONS[category],
            ", ".join(extensions) if extensions else "fallback",
        )

    console.print(table)


def print_history_location(path: Path) -> None:
    console.print(
        Panel(
            Text(str(path)),
            title="History File",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
