from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_secondary_contract_dialog.py"
RUNTIME = ROOT / "tools" / "smoke_runtime.py"
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"


def test_contract_smoke_targets_real_application_context() -> None:
    source = SMOKE.read_text(encoding="utf-8")
    runtime_source = RUNTIME.read_text(encoding="utf-8")
    entrypoint = ENTRYPOINT.read_text(encoding="utf-8")
    marker = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'

    assert marker in entrypoint
    assert f"MARKER_LINE = '{marker}'" in source
    assert "from smoke_runtime import" in source
    assert "run_entrypoint(" in source
    assert "write_diagnostic(" in source
    assert 'env["TEAMWORKS_SMOKE_MODE"] = "main-window"' in runtime_source
    assert 'env["PYTHONPATH"] = os.pathsep.join(search_paths)' in runtime_source
    assert 'compile(patched_source, str(PATCHED), "exec")' in source


def test_contract_smoke_exercises_forward_and_backward_navigation() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    assert "for _smoke_target_page in range(2, 7):" in source
    assert "_smoke_dialog.Onbouton_suite(None)" in source
    assert "for _smoke_target_page in range(5, 0, -1):" in source
    assert "_smoke_dialog.Onbouton_retour(None)" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_DIALOG_READY" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_DIALOG_FAILED" in source
    assert "PATCHED.unlink(missing_ok=True)" in source


@pytest.mark.skipif(sys.platform != "win32", reason="wxWidgets MSW requis")
def test_cee_rate_subdialog_is_constructible_with_wx33(monkeypatch) -> None:
    """Construit le sous-dialogue qui avait échappé au smoke de l'assistant parent."""
    teamworks_dir = str(ROOT / "teamworks")
    if teamworks_dir not in sys.path:
        sys.path.insert(0, teamworks_dir)

    import wx
    from Dlg import DLG_Config_cee_baremes

    class FakeDB:
        def IsTableExists(self, table_name):
            return True

        def ExecuterReq(self, request):
            self.request = request
            return "ok"

        def ResultatReq(self):
            return []

        def Close(self):
            pass

    monkeypatch.setattr(DLG_Config_cee_baremes.GestionDB, "DB", FakeDB)

    app = wx.GetApp()
    owns_app = app is None
    if owns_app:
        app = wx.App(False)
    frame = wx.Frame(None)
    dialog = None
    try:
        dialog = DLG_Config_cee_baremes.Dialog(frame)
        button_parent = dialog.bouton_ok.GetParent()
        assert button_parent is dialog.bouton_annuler.GetParent()
        assert button_parent.GetParent() is dialog
        dialog.Show()
        wx.Yield()
    finally:
        if dialog is not None:
            dialog.Destroy()
        frame.Destroy()
        wx.Yield()
        if owns_app:
            app.Destroy()


@pytest.mark.skipif(sys.platform != "win32", reason="wxWidgets MSW requis")
def test_contract_model_wizard_is_constructible_with_wx33(monkeypatch) -> None:
    """Construit les trois pages du modèle avec un schéma moderne minimal."""
    teamworks_dir = str(ROOT / "teamworks")
    if teamworks_dir not in sys.path:
        sys.path.insert(0, teamworks_dir)

    import wx
    from Dlg import DLG_Creation_modele_contrat

    class FakeDB:
        def __init__(self):
            self.request = ""

        def GetListeChamps2(self, table_name):
            if table_name == "contrats_modeles":
                return [
                    ("IDmodele", "INTEGER"),
                    ("nom", "VARCHAR(300)"),
                    ("description", "VARCHAR(400)"),
                    ("IDclassification", "INTEGER"),
                    ("IDtype", "INTEGER"),
                    ("cee_qualification", "VARCHAR(32)"),
                    ("convention_code", "VARCHAR(32)"),
                    ("ccns_group", "VARCHAR(8)"),
                ]
            return []

        def AjoutChamp(self, **kwargs):
            raise AssertionError("Le faux schéma contient déjà les colonnes TW-184")

        def ExecuterReq(self, request):
            self.request = request
            return "ok"

        def ResultatReq(self):
            query = self.request.lower()
            if "from contrats_types" in query:
                return [
                    (1, "CDD", "CDD", "non"),
                    (2, "Contrat d'engagement éducatif", "CEE", "non"),
                ]
            if "from contrats_class" in query:
                return [(1, "Classification historique")]
            if "from contrats_champs" in query:
                return []
            return []

        def Commit(self):
            pass

        def Close(self):
            pass

    monkeypatch.setattr(DLG_Creation_modele_contrat.GestionDB, "DB", FakeDB)

    app = wx.GetApp()
    owns_app = app is None
    if owns_app:
        app = wx.App(False)
    frame = wx.Frame(None)
    dialog = None
    try:
        dialog = DLG_Creation_modele_contrat.Dialog(frame, IDmodele=0)
        assert dialog.page1.GetParent() is dialog.panel_base
        assert dialog.page2.GetParent() is dialog.panel_base
        assert dialog.page3.GetParent() is dialog.panel_base
        dialog.Show()
        wx.Yield()
    finally:
        if dialog is not None:
            dialog.Destroy()
        frame.Destroy()
        wx.Yield()
        if owns_app:
            app.Destroy()
