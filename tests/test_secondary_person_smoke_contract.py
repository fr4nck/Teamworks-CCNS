from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_secondary_person_dialog.py"
MAILING_SMOKE = ROOT / "tools" / "smoke_mailing_preparation.py"
RUNTIME = ROOT / "tools" / "smoke_runtime.py"
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"
CORE = ROOT / "teamworks" / "Teamworks_core.py"


def test_person_smoke_targets_the_real_example_ready_marker() -> None:
    smoke_source = SMOKE.read_text(encoding="utf-8")
    runtime_source = RUNTIME.read_text(encoding="utf-8")
    entrypoint_source = ENTRYPOINT.read_text(encoding="utf-8")
    core_source = CORE.read_text(encoding="utf-8")
    marker = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'

    assert marker in core_source
    assert "import Teamworks_core as CORE" in entrypoint_source
    assert f"MARKER_LINE = '{marker}'" in smoke_source
    assert 'ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"' in smoke_source
    assert 'CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"' in smoke_source
    assert 'PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_secondary_person_smoke.py"' in smoke_source
    assert "import Teamworks_core_secondary_person_smoke as CORE" in smoke_source
    assert "from smoke_runtime import" in smoke_source
    assert "run_entrypoint(" in smoke_source
    assert "write_diagnostic(" in smoke_source
    assert 'env["TEAMWORKS_SMOKE_MODE"] = "main-window"' in runtime_source
    assert 'env["PYTHONPATH"] = os.pathsep.join(search_paths)' in runtime_source
    assert 'compile(patched_entrypoint, str(PATCHED), "exec")' in smoke_source
    assert 'compile(patched_core_source, str(PATCHED_CORE), "exec")' in smoke_source
    assert "PATCHED_CORE.unlink(missing_ok=True)" in smoke_source
    assert "timeout=240" in smoke_source


def test_person_smoke_covers_all_individual_pages() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    for label in (
        "Généralités",
        "Questionnaire",
        "Qualifications",
        "Contrats",
        "Présences",
        "Scénarios",
        "Frais",
        "Recrutement",
    ):
        assert f'"{label}"' in source

    assert "GetPageCount()" in source
    assert "SetSelection(_smoke_index)" in source
    assert "GetSize().GetWidth() > 0" in source
    assert "GetSize().GetHeight() > 0" in source
    assert "TEAMWORKS_SMOKE_PERSON_DIALOG_READY" in source
    assert "TEAMWORKS_SMOKE_PERSON_DIALOG_FAILED" in source
    assert "PATCHED.unlink(missing_ok=True)" in source


# Contrat CI : un dialogue de paramétrage exposé ne doit jamais être vide ou non construit.
def test_person_smoke_rejects_blank_parameter_dialogs() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    for marker in (
        "GetClientSize()",
        "GetChildren()",
        "IsShownOnScreen()",
        "contenu non construit",
        "aucun contrôle visible",
        "TEAMWORKS_SMOKE_PERSON_STAGE:parametrage",
        "TEAMWORKS_SMOKE_PARAMETER_OPEN:",
        "TEAMWORKS_SMOKE_PARAMETER_OK:",
    ):
        assert marker in source

    for label in (
        "Enregistrement",
        "Questionnaires",
        "Qualifications",
        "Types de pièces",
        "Situations",
        "Pays",
        "Catégories de présences",
        "Classifications",
        "Champs de contrats",
        "Modèles de contrats",
        "Types de contrats",
        "Valeurs de points",
        "Protection des entretiens",
        "Fonctions",
        "Affectations",
        "Diffuseurs",
        "Offres d'emploi",
        "Vacances",
        "Jours fériés",
    ):
        assert f'("{label}",' in source


def test_mailing_smoke_uses_real_mailer_without_network() -> None:
    source = MAILING_SMOKE.read_text(encoding="utf-8")

    assert "from Dlg import DLG_Mailer" in source
    assert "_smoke_dialog.OnBoutonEnvoyer(None)" in source
    assert "_smoke_email.Messagerie = lambda" in source
    assert "TEAMWORKS_SMOKE_MAILING_STAGE:first-send" in source
    assert "TEAMWORKS_SMOKE_MAILING_STAGE:second-send" in source
    assert "TEAMWORKS_SMOKE_MAILING_PREPARATION_READY" in source
    assert "ctrl_destinataires.donnees[0].pieces" in source


def test_mailing_preparation_runs_in_real_windows_application() -> None:
    if sys.platform != "win32":
        return

    completed = subprocess.run(
        [sys.executable, str(MAILING_SMOKE)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    assert completed.returncode == 0, output


def test_blackbox_hooks_real_wx_mainloop_on_windows(tmp_path, monkeypatch) -> None:
    if sys.platform != "win32":
        return

    teamworks_dir = ROOT / "teamworks"
    if str(teamworks_dir) not in sys.path:
        sys.path.insert(0, str(teamworks_dir))

    monkeypatch.setenv("TEAMWORKS_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("TEAMWORKS_FREEZE_THRESHOLD_SECONDS", "2")

    import wx
    from Utils import UTILS_Blackbox
    from Utils import UTILS_Rapport_bugs

    secret_label = "TW188_SENSITIVE_BUTTON_LABEL"
    UTILS_Blackbox.ViderChronologie()
    UTILS_Rapport_bugs.Activer_rapport_erreurs(version="tw188-windows-test")

    app = wx.App(redirect=False)
    frame = wx.Frame(None)
    button = wx.Button(frame, wx.ID_ANY, secret_label)
    frame.Show()

    def fire_event():
        event = wx.CommandEvent(wx.EVT_BUTTON.typeId, button.GetId())
        event.SetEventObject(button)
        wx.PostEvent(button, event)
        wx.CallLater(150, app.ExitMainLoop)

    wx.CallAfter(fire_event)
    app.MainLoop()

    timeline = UTILS_Blackbox.FormaterChronologie()
    assert UTILS_Rapport_bugs._BLACKBOX_FILTER is not None
    assert "BLACKBOX_START" in timeline
    assert "BUTTON_CLICK" in timeline
    assert secret_label not in timeline

    frame.Destroy()
    UTILS_Blackbox.ArreterWatchdog()
