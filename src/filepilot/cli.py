"""Typer command-line interface for FilePilot."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.text import Text

from . import __version__
from .core import organize_folder, plan_organize, scan_folder, undo_last_operation
from .history import get_history_file
from .rules import CATEGORY_ORDER, CATEGORY_RULES

app = typer.Typer(
    help="Safely organize and rename messy folders.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"FilePilot {__version__}")
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
        console.print(f"[red]Folder does not exist:[/red] {escape(str(folder))}")
        raise typer.Exit(code=1)
    if not folder.is_dir():
        console.print(f"[red]Path is not a folder:[/red] {escape(str(folder))}")
        raise typer.Exit(code=1)
    return folder.resolve()


@app.command()
def scan(folder: Path = typer.Argument(..., help="Folder to scan.")) -> None:
    """Scan a folder and summarize file categories."""
    target = _folder_argument(folder)
    result = scan_folder(target)

    table = Table(title=Text(f"FilePilot scan: {target}"))
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Files", justify="right", style="green")

    for category in CATEGORY_ORDER:
        table.add_row(category, str(result.counts[category]))

    console.print(table)
    console.print(f"[bold]Total files:[/bold] {len(result.files)}")


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

    if dry_run:
        planned = plan_organize(target)
        _print_moves(planned, title=f"Dry run: {target}")
        console.print("[yellow]No files were moved.[/yellow]")
        return

    try:
        planned, operation = organize_folder(target)
    except OSError as error:
        console.print(
            "[red]Could not prepare undo history, so no files were moved:[/red] "
            f"{escape(str(error))}"
        )
        raise typer.Exit(code=1) from error
    _print_moves(planned, title=f"Organized: {target}")
    if operation is None:
        console.print("[yellow]No files found to organize.[/yellow]")
    else:
        console.print("[green]Saved undo history:[/green] ", end="")
        console.print(Text(str(get_history_file())), end="")
        console.print(f" ([bold]{len(operation.moves)}[/bold] moves)")


def _print_moves(moves, title: str) -> None:
    table = Table(title=Text(title))
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Old file", overflow="fold")
    table.add_column("New location", style="green", overflow="fold")

    for move in moves:
        table.add_row(
            move.category,
            Text(move.source.name),
            Text(str(move.destination.relative_to(move.source.parent))),
        )

    console.print(table)
    console.print(f"[bold]Planned moves:[/bold] {len(moves)}")


@app.command()
def undo() -> None:
    """Undo the last organize operation."""
    try:
        operation, restored = undo_last_operation()
    except OSError as error:
        console.print(f"[red]Undo failed:[/red] {escape(str(error))}")
        raise typer.Exit(code=1) from error
    if operation is None:
        console.print("[yellow]No organize history found.[/yellow]")
        return

    table = Table(title=Text(f"Undo: {operation.created_at}"))
    table.add_column("Moved from", style="cyan", overflow="fold")
    table.add_column("Restored to", style="green", overflow="fold")

    for move in restored:
        table.add_row(Text(move.organized), Text(move.original))

    console.print(table)
    console.print(f"[green]Restored files:[/green] {len(restored)}")
    skipped = len(operation.moves) - len(restored)
    if skipped:
        console.print(
            f"[yellow]Skipped {skipped} missing files that were no longer present.[/yellow]"
        )


@app.command("config")
def show_config() -> None:
    """Show category rules and supported extensions."""
    table = Table(title="FilePilot category rules")
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Extensions", overflow="fold")

    for category in CATEGORY_ORDER:
        extensions = sorted(CATEGORY_RULES[category])
        table.add_row(category, ", ".join(extensions) if extensions else "fallback")

    console.print(table)
    console.print("[bold]History file:[/bold] ", end="")
    console.print(Text(str(get_history_file())))


if __name__ == "__main__":
    app()
