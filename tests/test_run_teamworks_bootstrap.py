from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "run_teamworks.py"


def load_launcher():
    spec = importlib.util.spec_from_file_location("run_teamworks", LAUNCHER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_root_launcher_exposes_modern_and_legacy_import_roots(monkeypatch):
    launcher = load_launcher()
    monkeypatch.setattr(sys, "path", ["sentinel"])

    launcher.configure_import_paths()

    assert str(launcher.ROOT) in sys.path
    assert str(launcher.TEAMWORKS_DIR) in sys.path
    assert "sentinel" in sys.path


def test_root_launcher_configuration_is_idempotent(monkeypatch):
    launcher = load_launcher()
    monkeypatch.setattr(sys, "path", [])

    launcher.configure_import_paths()
    launcher.configure_import_paths()

    assert sys.path.count(str(launcher.ROOT)) == 1
    assert sys.path.count(str(launcher.TEAMWORKS_DIR)) == 1


def test_root_launcher_executes_historical_entrypoint_as_main(monkeypatch):
    launcher = load_launcher()
    calls = []

    monkeypatch.setattr(launcher, "configure_import_paths", lambda: calls.append("paths"))
    monkeypatch.setattr(
        launcher.runpy,
        "run_path",
        lambda path, run_name: calls.append((path, run_name)),
    )

    assert launcher.main() == 0
    assert calls == [
        "paths",
        (str(launcher.ENTRYPOINT), "__main__"),
    ]
