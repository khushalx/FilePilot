from pathlib import Path, PureWindowsPath

from filepilot.rules import detect_category


def test_detects_known_categories_case_insensitively():
    assert detect_category(Path("photo.JPG")) == "images"
    assert detect_category(Path("report.PDF")) == "docs"
    assert detect_category(Path("app.py")) == "code"
    assert detect_category(Path("backup.zip")) == "archives"
    assert detect_category(Path("clip.mp4")) == "videos"
    assert detect_category(Path("song.MP3")) == "audio"


def test_unknown_extension_is_misc():
    assert detect_category(Path("mystery.blob")) == "misc"


def test_detects_category_from_windows_style_path():
    path = PureWindowsPath(r"C:\Users\Name\Downloads\Quarterly Report.PDF")

    assert detect_category(path) == "docs"
