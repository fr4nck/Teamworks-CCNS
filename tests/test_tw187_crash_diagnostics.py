from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
if str(TEAMWORKS) not in sys.path:
    sys.path.insert(0, str(TEAMWORKS))

from Utils import UTILS_Blackbox  # noqa: E402
from Utils import UTILS_Crash  # noqa: E402
from Utils import UTILS_Envoi_rapport_bug  # noqa: E402


def test_exception_report_is_written_with_runtime_context(tmp_path: Path) -> None:
    marker = "TW187_SENSITIVE_VALUE_42_50"
    try:
        raise RuntimeError(marker)
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
    assert "Exception: RuntimeError" in text
    assert marker not in text
    assert "aucune variable locale" in text
    assert "requête SQL" in text
    assert "contenu de base de données" in text


def test_crash_report_prefers_modern_version_file(tmp_path: Path, monkeypatch) -> None:
    runtime = tmp_path / "teamworks"
    runtime.mkdir()
    (tmp_path / "VERSION").write_text("0.9.0-dev\n", encoding="utf-8")
    monkeypatch.setattr(UTILS_Crash, "_repertoire_principal", lambda: str(runtime))

    try:
        raise RuntimeError("version-check")
    except RuntimeError:
        exctype, value, tb = sys.exc_info()
        path = UTILS_Crash.EcrireRapportException(
            exctype,
            value,
            tb,
            version="2.1.3.1",
            repertoire=str(tmp_path / "logs"),
        )

    text = Path(path).read_text(encoding="utf-8")
    assert "Version application: 0.9.0-dev" in text
    assert "Version application: 2.1.3.1" not in text


def test_early_hook_captures_import_time_style_crash_without_message(tmp_path: Path) -> None:
    marker = "TW187_EARLY_SENSITIVE"
    code = "\n".join(
        [
            "import sys",
            f"sys.path.insert(0, {str(TEAMWORKS)!r})",
            "import Chemins",
            f"raise RuntimeError({marker!r})",
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
    assert "Exception: RuntimeError" in text
    assert marker not in text
    assert marker not in completed.stderr


def test_safe_import_error_keeps_only_technical_module_name(tmp_path: Path) -> None:
    try:
        import definitely_missing_tw187_module  # noqa: F401
    except ModuleNotFoundError:
        exctype, value, tb = sys.exc_info()
        path = UTILS_Crash.EcrireRapportException(
            exctype,
            value,
            tb,
            contexte="Import test",
            repertoire=str(tmp_path),
        )

    text = Path(path).read_text(encoding="utf-8")
    assert "Exception: ModuleNotFoundError | module=definitely_missing_tw187_module" in text
    assert "No module named" not in text


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


def test_crash_report_embeds_only_blackbox_technical_breadcrumbs(tmp_path: Path) -> None:
    UTILS_Blackbox.ViderChronologie()
    UTILS_Blackbox.Tracer("MENU", "menu:contrats_types", code=123)
    UTILS_Blackbox.Tracer("DOUBLE_CLICK", "wx:Ol.OL_contrats.ListView", code=456)

    try:
        raise KeyError("family-sensitive-key")
    except KeyError:
        exctype, value, tb = sys.exc_info()
        path = UTILS_Crash.EcrireRapportException(
            exctype,
            value,
            tb,
            contexte="Breadcrumbs",
            repertoire=str(tmp_path),
        )

    text = Path(path).read_text(encoding="utf-8")
    assert "menu:contrats_types" in text
    assert "wx:Ol.OL_contrats.ListView" in text
    assert "family-sensitive-key" not in text


def test_crash_dialog_source_exposes_logs_folder() -> None:
    source = (TEAMWORKS / "Utils" / "UTILS_Rapport_bugs.py").read_text(encoding="utf-8")
    assert "Ouvrir le dossier Logs" in source
    assert "Copier le rapport" in source
    assert "Envoyer le rapport" in source
    assert "UTILS_Envoi_rapport_bug.EnvoyerRapport" in source
    assert "Boucle wxPython" in source
    assert "threading.excepthook" in source


def test_bug_report_email_uses_fixed_recipient_and_safe_attachment(tmp_path: Path) -> None:
    report = tmp_path / "crash-test.txt"
    report.write_text("rapport technique sûr", encoding="utf-8")
    calls = []

    class FakeMessage:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class FakeMailer:
        def Connecter(self):
            calls.append("connect")

        def Envoyer(self, message):
            calls.append(message)
            return True

        def Fermer(self):
            calls.append("close")

    class FakeEmailModule:
        Message = FakeMessage

        @staticmethod
        def GetAdresseExpDefaut():
            return {
                "moteur": "smtp",
                "smtp": "smtp.example.test",
                "port": 587,
                "utilisateur": "sender",
                "motdepasse": "secret",
                "adresse": "sender@example.test",
                "nom_adresse": "Teamworks",
                "startTLS": True,
                "parametres": None,
            }

        @staticmethod
        def Messagerie(**kwargs):
            calls.append(kwargs)
            return FakeMailer()

    recipient = UTILS_Envoi_rapport_bug.EnvoyerRapport(
        str(report),
        version="0.9-test",
        module_email=FakeEmailModule,
    )

    assert recipient == "multimedia@pelemele.org"
    message = next(call for call in calls if isinstance(call, FakeMessage))
    assert message.destinataires == ["multimedia@pelemele.org"]
    assert message.fichiers == [str(report)]
    assert "0.9-test" in message.sujet
    assert calls[-1] == "close"


def test_bug_report_email_requires_configured_sender(tmp_path: Path) -> None:
    report = tmp_path / "crash-test.txt"
    report.write_text("rapport", encoding="utf-8")

    class NoSenderEmailModule:
        @staticmethod
        def GetAdresseExpDefaut():
            return None

    try:
        UTILS_Envoi_rapport_bug.EnvoyerRapport(
            str(report), module_email=NoSenderEmailModule
        )
    except UTILS_Envoi_rapport_bug.ErreurEnvoiRapport as err:
        assert "expéditeur" in str(err)
    else:
        raise AssertionError("Une configuration expéditeur absente doit bloquer l'envoi")
