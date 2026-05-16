"""Typer command-line interface for FilePilot."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.markup import escape

from . import __version__, ui
from .core import organize_folder, plan_organize, scan_folder, undo_last_operation
from .history import get_history_file, peek_last_operation

app = typer.Typer(
    help="Safely organize and rename messy folders.",
    no_args_is_help=True,
)
console = ui.console


def version_callback(value: bool) -> None:
    if value:
        ui.print_header("Version")
        console.print(f"[bold]FilePilot {__version__}[/bold]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the FilePilot version.",
    ),
) -> None:
    """FilePilot keeps folder cleanup safe, visible, and undoable."""


def _folder_argument(folder: Path) -> Path:
    if not folder.exists():
        ui.print_header("Path Check")
        ui.print_error(f"Folder does not exist: {escape(str(folder))}")
        raise typer.Exit(code=1)
    if not folder.is_dir():
        ui.print_header("Path Check")
        ui.print_error(f"Path is not a folder: {escape(str(folder))}")
        raise typer.Exit(code=1)
    return folder.resolve()


@app.command()
def scan(folder: Path = typer.Argument(..., help="Folder to scan.")) -> None:
    """Scan a folder and summarize file categories."""
    target = _folder_argument(folder)
    ui.print_header("Scan", target)

    result = scan_folder(target)
    if not result.files:
        ui.print_empty_state(
            "Nothing To Scan",
            "This folder has no direct child files. FilePilot is ready when files arrive.",
        )
        return

    ui.print_scan_summary(result)
    ui.print_category_table(result.counts)


@app.command()
def organize(
    folder: Path = typer.Argument(..., help="Folder to organize."),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview changes without moving files.",
    ),
) -> None:
    """Organize files into category folders with safe cleaned names."""
    target = _folder_argument(folder)
    ui.print_header("Dry Run" if dry_run else "Organize", target)

    planned = plan_organize(target)
    if not planned:
        ui.print_empty_state(
            "Nothing To Organize",
            "This folder has no direct child files to move. No changes were made.",
        )
        return

    if dry_run:
        ui.print_dry_run_intro()
        ui.print_move_preview(planned)
        ui.print_dry_run_summary(planned)
        return

    folders_created = len(ui.folders_needed(planned))
    conflicts_handled = ui.conflict_safe_renames(planned)
    ui.print_safety_check()

    progress = ui.make_progress("Organizing files")
    try:
        with progress:
            task_id = progress.add_task("organize", total=len(planned))

            def advance(_move) -> None:
                progress.advance(task_id)

            _planned, operation = organize_folder(target, progress_callback=advance)
    except OSError as error:
        ui.print_error(
            "Could not prepare undo history, so no files were moved: "
            f"{escape(str(error))}"
        )
        raise typer.Exit(code=1) from error

    ui.print_cleanup_complete(
        files_organized=len(operation.moves) if operation is not None else 0,
        folders_created=folders_created,
        conflicts_handled=conflicts_handled,
        undo_available=operation is not None,
    )
    ui.print_move_preview(_planned, title="Organized Files")


@app.command()
def undo() -> None:
    """Undo the last organize operation."""
    ui.print_header("Undo")
    operation_preview = peek_last_operation()
    if operation_preview is None:
        ui.print_empty_state(
            "No Undo History",
            f"No organize history was found at {get_history_file()}.",
        )
        return

    ui.print_restore_mode()
    progress = ui.make_progress("Restoring files")
    try:
        with progress:
            task_id = progress.add_task("restore", total=len(operation_preview.moves))

            def advance(_move, _restored) -> None:
                progress.advance(task_id)

            operation, restored = undo_last_operation(progress_callback=advance)
    except OSError as error:
        ui.print_error(f"Undo failed: {escape(str(error))}")
        raise typer.Exit(code=1) from error

    if operation is None:
        ui.print_empty_state(
            "No Undo History",
            f"No organize history was found at {get_history_file()}.",
        )
        return

    original_by_organized = {move.organized: move.original for move in operation.moves}
    conflicts_handled = sum(
        1
        for move in restored
        if move.original != original_by_organized.get(move.organized, move.original)
    )
    ui.print_restore_table(restored)
    ui.print_restore_summary(
        files_restored=len(restored),
        conflicts_handled=conflicts_handled,
        history_updated=True,
    )
    skipped = len(operation.moves) - len(restored)
    if skipped:
        ui.print_empty_state(
            "Missing Files Skipped",
            f"{skipped} file(s) were no longer present, so FilePilot left them untouched.",
        )


@app.command("config")
def show_config() -> None:
    """Show category rules and supported extensions."""
    ui.print_header("Config")
    ui.print_config_table()
    ui.print_history_location(get_history_file())


if __name__ == "__main__":
    app()
