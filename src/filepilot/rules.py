"""Category rules for FilePilot."""

from __future__ import annotations

from collections import Counter
from pathlib import Path, PurePath

CATEGORY_RULES: dict[str, set[str]] = {
    "docs": {
        ".csv",
        ".doc",
        ".docx",
        ".epub",
        ".md",
        ".odt",
        ".pdf",
        ".ppt",
        ".pptx",
        ".rtf",
        ".txt",
        ".xls",
        ".xlsx",
    },
    "images": {
        ".avif",
        ".bmp",
        ".gif",
        ".heic",
        ".jpeg",
        ".jpg",
        ".png",
        ".svg",
        ".tif",
        ".tiff",
        ".webp",
    },
    "code": {
        ".c",
        ".cpp",
        ".css",
        ".go",
        ".html",
        ".java",
        ".js",
        ".json",
        ".jsx",
        ".php",
        ".py",
        ".rb",
        ".rs",
        ".sh",
        ".sql",
        ".swift",
        ".toml",
        ".ts",
        ".tsx",
        ".xml",
        ".yaml",
        ".yml",
    },
    "archives": {
        ".7z",
        ".bz2",
        ".gz",
        ".rar",
        ".tar",
        ".tgz",
        ".xz",
        ".zip",
    },
    "videos": {
        ".avi",
        ".m4v",
        ".mkv",
        ".mov",
        ".mp4",
        ".mpeg",
        ".mpg",
        ".webm",
        ".wmv",
    },
    "audio": {
        ".aac",
        ".aiff",
        ".flac",
        ".m4a",
        ".mp3",
        ".ogg",
        ".wav",
        ".wma",
    },
    "misc": set(),
}

CATEGORY_ORDER = ("docs", "images", "code", "archives", "videos", "audio", "misc")


def detect_category(path: Path | PurePath | str) -> str:
    """Return the category for a file path based on its extension."""
    suffix = Path(path).suffix.lower()
    for category in CATEGORY_ORDER:
        if category == "misc":
            continue
        if suffix in CATEGORY_RULES[category]:
            return category
    return "misc"


def category_counts(files: list[Path]) -> Counter[str]:
    counts: Counter[str] = Counter({category: 0 for category in CATEGORY_ORDER})
    counts.update(detect_category(file) for file in files)
    return counts
