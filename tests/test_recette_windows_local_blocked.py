import json
from pathlib import Path
import shutil
import subprocess

import pytest

from tools.recette_windows import cli
from tools.recette_windows.errors import BlockedEnvironment, UnsupportedRunner


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "run_recette_windows.ps1"


def test_unsupported_runner_is_an_explicit_blocked_environment():
    assert issubclass(UnsupportedRunner, BlockedEnvironment)


def test_cli_serializes_blocked_without_counting_it_as_teamworks_failure(monkeypatch, tmp_path):
    class FakeDriver:
        def __init__(self, root, artifacts_dir, timeout, backend):
            self.root = root
            self.artifacts_dir = Path(artifacts_dir)
            self.artifacts_dir.mkdir(parents=True, exist_ok=True)
            self.process = None

        def start(self):
            raise UnsupportedRunner("session Windows non interactive")

        def capture_failure(self, exc):
            (self.artifacts_dir / "failure.txt").write_text(str(exc), encoding="utf-8")

    monkeypatch.setattr(cli, "WindowsRecipeDriver", FakeDriver)

    code = cli.main(
        [
            "--scenario",
            "individus-smoke",
            "--artifacts",
            str(tmp_path),
        ]
    )

    assert code == 4
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert result["status"] == "BLOCKED"
    assert result["exit_status"] == 4
    assert "session Windows non interactive" in result["error"]
    assert "session Windows non interactive" in (tmp_path / "failure.txt").read_text(encoding="utf-8")


def test_root_wrapper_keeps_one_command_and_exact_final_verdicts():
    source = WRAPPER.read_text(encoding="utf-8")

    for marker in (
        "tools\\recette_windows\\run_local.ps1",
        '$Scenario = "individus-smoke"',
        '$Status = "BLOCKED"',
        '$Verdict = "RECETTE OK"',
        '$Verdict = "RECETTE KO"',
        '$Verdict = "ENVIRONNEMENT NON QUALIFIABLE"',
        "launcher-output.log",
        "launcher-result.json",
        "RESULTATS:",
    ):
        assert marker in source

    assert "Noethys" not in source
    assert "WM_CLOSE" not in source


def test_root_wrapper_powershell_parses_when_pwsh_is_available():
    pwsh = shutil.which("pwsh")
    if not pwsh:
        pytest.skip("pwsh indisponible sur ce runner")

    completed = subprocess.run(
        [
            pwsh,
            "-NoProfile",
            "-Command",
            "[scriptblock]::Create((Get-Content -Raw $args[0])) | Out-Null",
            str(WRAPPER),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
