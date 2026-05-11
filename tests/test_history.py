from pathlib import Path

from filepilot.history import get_app_dir, get_history_file


def test_default_history_uses_path_home(monkeypatch):
    fake_home = Path("fake-home")

    monkeypatch.delenv("FILEPILOT_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    assert get_app_dir() == fake_home / ".filepilot"
    assert get_history_file() == fake_home / ".filepilot" / "history.json"


def test_history_home_override_uses_path(monkeypatch):
    configured_home = r"C:\Temp\filepilot-history"

    monkeypatch.setenv("FILEPILOT_HOME", configured_home)

    assert get_app_dir() == Path(configured_home)
    assert get_history_file() == Path(configured_home) / "history.json"
