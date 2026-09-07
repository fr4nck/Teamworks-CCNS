from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRESENCE_DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_presence.py"


def _source():
    return PRESENCE_DIALOG.read_text(encoding="utf-8")


def test_presence_entry_keeps_modern_dialog_structure():
    source = _source()
    assert "class Dialog(wx.Dialog):" in source
    assert "class ListCtrl_donnees" in source
    assert "class CTRL_Selection_personnes" in source
    assert "self.SetSizer" in source
    assert "self.CentreOnScreen()" in source


def test_presence_entry_keeps_people_selection_contract():
    source = _source()
    assert "self.ctrl_personnes" in source
    assert "GetPersonnesSelectionnees" in source
    assert "GetIDpersonnes" in source
    assert "self.dictDonnees" in source


def test_presence_entry_keeps_date_and_time_controls():
    source = _source()
    assert "self.ctrl_date" in source
    assert "self.ctrl_heure_debut" in source
    assert "self.ctrl_heure_fin" in source
    assert "self.ctrl_categorie" in source


def test_presence_entry_keeps_model_and_selection_refresh_contract():
    source = _source()
    assert 'if hasattr(self, "listCtrl_donnees"):' in source
    assert "self.listCtrl_donnees.SetDonnees(self.dictDonnees)" in source
    assert "def SetDonnees(self, dictDonnees):" in source
    assert "self.Remplissage()" in source
    assert "self.owner.UpdateSelectionSummary()" in source


def test_presence_entry_keeps_validation_and_persistence_contract():
    source = _source()
    for method in (
        "ValidationDonnees",
        "SauvegardeModif",
        "SauvegardeNouveau",
        "GetDonneesModele",
        "ImportPersonnes",
        "ImportDonneesModif",
    ):
        assert "def %s" % method in source
    assert 'DB.ReqMAJ("presences"' in source
    assert 'DB.ReqInsert("presences", listeDonnees, commit=False)' in source
    assert "DB.Commit()" in source
    assert "DB.connexion.rollback()" in source
    assert "UTILS_Presences.normaliser_intitule_presence" in source
