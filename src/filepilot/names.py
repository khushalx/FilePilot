"""Filename cleaning and collision-safe path helpers."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

NOISE_WORDS = {
    "copy",
    "duplicate",
    "final",
    "finalfinal",
    "new",
    "old",
}
UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._ -]+")
BRACKET_CHARS = str.maketrans({
    "(": " ",
    ")": " ",
    "[": " ",
    "]": " ",
    "{": " ",
    "}": " ",
})
SEPARATORS = re.compile(r"[\s._-]+")


def clean_filename_stem(stem: str) -> str:
    """Clean a filename stem while keeping it readable and portable."""
    normalized = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode()
    normalized = normalized.translate(BRACKET_CHARS)
    normalized = UNSAFE_CHARS.sub(" ", normalized)

    parts: list[str] = []
    seen: set[str] = set()
    for raw_part in SEPARATORS.split(normalized):
        part = raw_part.strip().lower()
        if not part:
            continue
        if part in NOISE_WORDS:
            continue
        # Drop obvious duplicates such as "report report", but preserve numbers.
        if part in seen and not part.isdigit():
            continue
        seen.add(part)
        parts.append(part)

    return "-".join(parts) or "untitled"


def dated_filename(path: Path, date_prefix: str) -> str:
    cleaned = clean_filename_stem(path.stem)
    return f"{date_prefix}_{cleaned}{path.suffix.lower()}"


def unique_path(destination: Path, reserved: set[Path] | None = None) -> Path:
    """Return a path that does not exist and is not already reserved."""
    reserved = reserved or set()
    candidate = destination
    counter = 1

    while candidate.exists() or candidate in reserved:
        candidate = destination.with_name(
            f"{destination.stem}_{counter}{destination.suffix}"
        )
        counter += 1

    return candidate

