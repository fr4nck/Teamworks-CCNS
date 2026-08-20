from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
if str(TEAMWORKS) not in sys.path:
    sys.path.insert(0, str(TEAMWORKS))

from Utils import UTILS_Crash  # noqa: E402


def test_exception_report_is_written_with_runtime_context(tmp_path: Path) -> None:
    try:
        raise RuntimeError("TW187 boom")
    except RuntimeError:
        exctype, value, tb = sys.exc_info()
        path = UTILS_Crash.EcrireRapportException(
            exctype,
            value,
            tb,
            version="0.9-test",
            contexte="Test contrôlé",
            version_wx="4.3-test",
            repertoire=str(tmp_path),
        )

    report = Path(path)
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    assert "Teamworks CCNS — rapport de crash" in text
    assert "Version application: 0.9-test" in text
    assert "Contexte: Test contrôlé" in text
    assert "wxPython: 4.3-test" in text
    assert "RuntimeError: TW187 boom" in text
    assert "variables d'environnement" in text


def test_early_hook_captures_import_time_style_crash(tmp_path: Path) -> None:
    code = "\n".join(
        [
            "import sys",
            f"sys.path.insert(0, {str(TEAMWORKS)!r})",
            "import Chemins",
            "raise RuntimeError('TW187 early crash')",
        ]
    )
    env = os.environ.copy()
    env["TEAMWORKS_LOG_DIR"] = str(tmp_path)

    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert completed.returncode != 0
    reports = sorted(tmp_path.glob("crash-*.txt"))
    assert reports, completed.stderr
    text = reports[-1].read_text(encoding="utf-8")
    assert "Contexte: Démarrage / import" in text
    assert "RuntimeError: TW187 early crash" in text


def test_report_does_not_dump_environment_values(tmp_path: Path, monkeypatch) -> None:
    marker = "TW187_SECRET_SHOULD_NOT_APPEAR"
    monkeypatch.setenv("TW187_SECRET", marker)

    try:
        raise ValueError("safe failure")
    except ValueError:
        exctype, value, tb = sys.exc_info()
        path = UTILS_Crash.EcrireRapportException(
            exctype,
            value,
            tb,
            contexte="Confidentialité",
            repertoire=str(tmp_path),
        )

    text = Path(path).read_text(encoding="utf-8")
    assert marker not in text


def test_crash_dialog_source_exposes_logs_folder() -> None:
    source = (TEAMWORKS / "Utils" / "UTILS_Rapport_bugs.py").read_text(encoding="utf-8")
    assert "Ouvrir le dossier Logs" in source
    assert "Copier le rapport" in source
    assert "Boucle wxPython" in source
    assert "threading.excepthook" in source
