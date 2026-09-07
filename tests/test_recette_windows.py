import json
import os
from pathlib import Path
import shutil
import subprocess
import types

import pytest

from tools.recette_windows import cli
from tools.recette_windows.driver import WindowsRecipeDriver
from tools.recette_windows.errors import DestructiveDialogDetected
from tools.recette_windows.guards import (
    assert_not_destructive,
    looks_destructive,
    looks_like_destructive_confirmation,
    normalize_text,
)
from tools.recette_windows.selectors import find_named


ROOT = Path(__file__).resolve().parents[1]
RUN_LOCAL = ROOT / "tools" / "recette_windows" / "run_local.ps1"


class FakeElement:
    def __init__(self, name, control_type="Pane", visible=True, enabled=True):
        self.element_info = types.SimpleNamespace(name=name, control_type=control_type)
        self._visible = visible
        self._enabled = enabled

    def window_text(self):
        return self.element_info.name

    def is_visible(self):
        return self._visible

    def is_enabled(self):
        return self._enabled


def test_normalize_text_is_accent_and_space_insensitive():
    assert normalize_text("  État   des dossiers ") == "etat des dossiers"


def test_destructive_guard_rejects_delete_confirmation():
    assert looks_destructive(["Confirmer la suppression de cette fiche ?"])
    assert looks_like_destructive_confirmation(["Confirmer la suppression de cette fiche ?"])
    with pytest.raises(DestructiveDialogDetected):
        assert_not_destructive(["Supprimer définitivement"], context="test")


def test_destructive_guard_allows_safe_options_dialog():
    texts = ["Options", "Colonnes visibles", "OK", "Annuler"]
    assert not looks_destructive(texts)
    assert not looks_like_destructive_confirmation(texts)
    assert_not_destructive(texts)


def test_delete_button_alone_is_not_mistaken_for_confirmation_dialog():
    assert looks_destructive(["Supprimer"])
    assert not looks_like_destructive_confirmation(["Fiche individuelle", "Supprimer"])


def test_find_named_prefers_visible_enabled_exact_match():
    hidden = FakeElement("Individus", visible=False)
    good = FakeElement("Individus", control_type="Button")
    assert find_named([hidden, good], " individus ") is good


def test_find_named_can_filter_control_type():
    pane = FakeElement("OL_personnes", control_type="Pane")
    list_view = FakeElement("OL_personnes", control_type="List")
    assert find_named([pane, list_view], "OL_personnes", control_types=("List",)) is list_view


def test_local_runner_is_one_command_and_keeps_recipe_dependencies_separate():
    source = RUN_LOCAL.read_text(encoding="utf-8")

    for marker in (
        '$Scenario = "individus-smoke"',
        "SESSIONNAME",
        "UserInteractive",
        "GetInputDesktopName",
        "SessionId",
        "Get-Python311",
        "run_teamworks.py",
        "import wx",
        "requirements\\recette-windows.txt",
        '"-m", "pip", "install"',
        '"-m", "tools.recette_windows"',
        "Compress-Archive",
        "RECETTE OK",
        "RECETTE KO",
        "ENVIRONNEMENT NON PRÊT",
        "GetCurrentProcessDpiAwareness",
        "GetDpiForSystem",
        "system_scaling_percent",
        "environment.json",
        "local-run.json",
    ):
        assert marker in source

    assert "requirements\\python311-core.txt" not in source
    assert "TEAMWORKS_SMOKE_MODE" not in source


def test_local_runner_powershell_parses_when_pwsh_is_available():
    pwsh = shutil.which("pwsh")
    if not pwsh:
        pytest.skip("pwsh indisponible sur ce runner")

    env = os.environ.copy()
    env["TEAMWORKS_RUN_LOCAL_PS1"] = str(RUN_LOCAL)
    completed = subprocess.run(
        [
            pwsh,
            "-NoProfile",
            "-Command",
            "[scriptblock]::Create((Get-Content -Raw $env:TEAMWORKS_RUN_LOCAL_PS1)) | Out-Null",
        ],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr


def test_cli_always_writes_result_manifest_and_window_dump(monkeypatch, tmp_path):
    trace = [
        {
            "start": {"name": "Individus"},
            "key": "TAB",
            "received": {"name": "Liste"},
            "result": "OK",
        }
    ]

    class FakeDriver:
        def __init__(self, root, artifacts_dir, timeout, backend):
            self.root = root
            self.artifacts_dir = Path(artifacts_dir)
            self.artifacts_dir.mkdir(parents=True, exist_ok=True)
            self.process = object()

        def start(self):
            return 123

        def dump_windows(self):
            (self.artifacts_dir / "windows.txt").write_text("fake-window", encoding="utf-8")

        def shutdown(self, graceful=True):
            return 0

    def fake_scenario(driver):
        (driver.artifacts_dir / "keyboard-focus.json").write_text(
            json.dumps(trace), encoding="utf-8"
        )
        return {
            "scenario": "individus-smoke",
            "action": "fake action",
            "keyboard": trace,
        }

    monkeypatch.setattr(cli, "WindowsRecipeDriver", FakeDriver)
    monkeypatch.setitem(cli.SCENARIOS, "individus-smoke", fake_scenario)

    code = cli.main(
        [
            "--scenario",
            "individus-smoke",
            "--artifacts",
            str(tmp_path),
        ]
    )

    assert code == 0
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert result["status"] == "ok"
    assert result["exit_status"] == 0
    assert result["keyboard"] == trace
    assert (tmp_path / "windows.txt").read_text(encoding="utf-8") == "fake-window"


def test_driver_collects_recent_windows_appdata_logs(monkeypatch, tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    appdata = tmp_path / "appdata"
    log_dir = appdata / "teamworks"
    log_dir.mkdir(parents=True)
    (log_dir / "journal.log").write_text("journal recette", encoding="utf-8")

    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setattr("tools.recette_windows.driver.platform.system", lambda: "Windows")

    driver = WindowsRecipeDriver(root, tmp_path / "artifacts")
    driver.started_at = 0.0
    assert driver.collect_logs() == 1
    assert (driver.artifacts_dir / "app-logs" / "journal.log").read_text(encoding="utf-8") == "journal recette"


def test_close_dialog_reports_escape_or_cleanup_fallback(tmp_path):
    driver = WindowsRecipeDriver(tmp_path, tmp_path / "artifacts")
    window = types.SimpleNamespace(handle=42, set_focus=lambda: None, close=lambda: None)
    driver.guard_window = lambda target: None
    driver.send_escape = lambda: None

    driver._wait_handle_gone = lambda handle, timeout: True
    assert driver.close_dialog(window) == "escape"

    calls = iter((False, True))
    driver._wait_handle_gone = lambda handle, timeout: next(calls)
    assert driver.close_dialog(window) == "wm_close"
