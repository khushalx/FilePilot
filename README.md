# FilePilot

FilePilot is a beginner-friendly, production-minded Python CLI for cleaning messy folders safely. It scans files, previews changes, organizes them into category folders, renames them with readable date-prefixed names, and keeps a JSON history so the latest organize operation can be undone.

It is designed around three promises:

- Never delete files
- Never overwrite files
- Always let you preview before moving anything

## Features

- Scan a folder and see counts for `docs`, `images`, `code`, `archives`, `videos`, `audio`, and `misc`
- Preview organization with `--dry-run`
- Organize top-level files into automatically created category folders
- Rename files with `YYYY-MM-DD_clean-original-name.extension`
- Clean filenames by removing extra spaces, brackets, unsafe characters, repeated words, and common noise words like `copy` and `final`
- Avoid collisions with `_1`, `_2`, and so on
- Undo the last organize operation using a JSON history file
- Clean Rich-powered terminal tables

## Installation

Clone the project and install it in editable mode.

macOS and Linux:

```bash
git clone https://github.com/khushalx/FilePilot.git
cd filepilot
python -m pip install -e .
```

Windows PowerShell:

```powershell
git clone https://github.com/khushalx/FilePilot.git
cd filepilot
py -m pip install -e .
```

For development and tests:

```bash
python -m pip install -e ".[dev]"
pytest
```

## Usage

### Scan a Folder

```bash
filepilot scan ~/Downloads
```

Windows PowerShell or Command Prompt:

```powershell
filepilot scan "C:\Users\Name\Downloads"
```

Example output:

```text
              FilePilot scan: /Users/you/Downloads
┏━━━━━━━━━━━┳━━━━━━━┓
┃ Category  ┃ Files ┃
┡━━━━━━━━━━━╇━━━━━━━┩
│ docs      │    12 │
│ images    │    24 │
│ code      │     3 │
│ archives  │     4 │
│ videos    │     2 │
│ audio     │     1 │
│ misc      │     6 │
└───────────┴───────┘
Total files: 52
```

### Preview an Organize Operation

```bash
filepilot organize ~/Downloads --dry-run
```

Windows PowerShell or Command Prompt:

```powershell
filepilot organize "C:\Users\Name\Downloads" --dry-run
```

Example output:

```text
                         Dry run: /Users/you/Downloads
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Category ┃ Old file                     ┃ New location                       ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ docs     │ Final Report (copy).PDF      │ docs/2026-05-11_report.pdf         │
│ images   │ vacation photo [final].JPG   │ images/2026-05-10_vacation-photo.jpg │
│ archives │ backup.zip                   │ archives/2026-05-09_backup.zip      │
└──────────┴──────────────────────────────┴────────────────────────────────────┘
Planned moves: 3
No files were moved.
```

### Organize a Folder

```bash
filepilot organize ~/Downloads
```

Windows PowerShell or Command Prompt:

```powershell
filepilot organize "C:\Users\Name\Downloads"
```

FilePilot moves direct child files into category folders:

```text
~/Downloads/
  docs/
    2026-05-11_report.pdf
  images/
    2026-05-10_vacation-photo.jpg
  archives/
    2026-05-09_backup.zip
```

If a destination already exists, FilePilot chooses the next safe name:

```text
docs/2026-05-11_report.pdf
docs/2026-05-11_report_1.pdf
docs/2026-05-11_report_2.pdf
```

### Undo the Last Organize Operation

```bash
filepilot undo
```

Undo uses a JSON history file stored at:

```text
~/.filepilot/history.json
```

On Windows, this resolves through `Path.home()` to a path like:

```text
C:\Users\Name\.filepilot\history.json
```

If the original location is already occupied during undo, FilePilot still does not overwrite it. It restores the file with a safe suffix instead.

For tests, CI, or locked-down environments, set `FILEPILOT_HOME` to choose a different history directory:

macOS and Linux:

```bash
FILEPILOT_HOME=/tmp/filepilot-history filepilot organize ~/Downloads
```

Windows PowerShell:

```powershell
$env:FILEPILOT_HOME = "C:\Temp\filepilot-history"
filepilot organize "C:\Users\Name\Downloads"
```

Windows Command Prompt:

```bat
set FILEPILOT_HOME=C:\Temp\filepilot-history
filepilot organize "C:\Users\Name\Downloads"
```

### Show Supported Extensions

```bash
filepilot config
```

## Category Rules

| Category | Examples |
| --- | --- |
| docs | `.pdf`, `.docx`, `.txt`, `.md`, `.xlsx`, `.pptx` |
| images | `.jpg`, `.png`, `.gif`, `.svg`, `.webp`, `.heic` |
| code | `.py`, `.js`, `.ts`, `.html`, `.css`, `.json`, `.yaml` |
| archives | `.zip`, `.rar`, `.tar`, `.gz`, `.7z` |
| videos | `.mp4`, `.mov`, `.mkv`, `.webm`, `.avi` |
| audio | `.mp3`, `.wav`, `.flac`, `.m4a`, `.ogg` |
| misc | Anything else |

## Design Notes

FilePilot currently organizes only the direct files inside the folder you pass in. It does not recursively move files from nested directories. This keeps the first version predictable and safer for real folders like `Downloads`.

The modification date of each file is used for the `YYYY-MM-DD` prefix.

FilePilot uses Python's `pathlib.Path` for filesystem paths, so Windows paths such as `C:\Users\Name\Downloads`, macOS paths such as `/Users/name/Downloads`, and Linux paths such as `/home/name/Downloads` are handled by the operating system's native path rules.

## Project Structure

```text
filepilot/
  pyproject.toml
  README.md
  src/filepilot/
    cli.py
    core.py
    history.py
    names.py
    rules.py
  tests/
    test_names.py
    test_rules.py
```

## License

MIT
