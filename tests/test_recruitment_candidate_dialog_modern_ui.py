import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_candidat.py"
CORE = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_candidat_core.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_candidate_shell_and_core_are_valid_python():
    ast.parse(_source(SHELL))
    ast.parse(_source(CORE))


def test_candidate_keeps_historical_business_engine():
    shell = _source(SHELL)
    core = _source(CORE)
    assert "from Dlg import DLG_Saisie_candidat_core as CORE" in shell
    assert "class Panel(CORE.Panel):" in shell
    for method in (
        "CreationIDfiche",
        "Sauvegarde",
        "Onbouton_annuler",
        "OnBoutonConvertir",
        "Onbouton_courrier",
        "OnBoutonQualifications",
    ):
        assert "def %s" % method in core
    for table in ("candidats", "coords_candidats", "diplomes_candidats", "candidatures", "entretiens"):
        assert table in core


def test_candidate_uses_seven_semantic_sections_and_workspace():
    source = _source(SHELL)
    assert source.count("CTRL_Section.Section(") == 7
    for title in ("Identité", "Adresse", "Coordonnées", "Qualifications", "Candidatures", "Entretiens", "Mémo"):
        assert title in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "workspace")' in source


def test_candidate_has_no_legacy_chrome():
    source = _source(SHELL)
    for legacy in (
        "wx.StaticBox",
        "wx.FlexGridSizer",
        "wx.BitmapButton",
        ".Fit(self)",
        "wx.ImageList",
        "TestPopup",
        "Images/16x16",
        "(236, 233, 216)",
        "wx.SUNKEN_BORDER",
    ):
        assert legacy not in source


def test_candidate_contact_and_qualification_lists_are_textual_and_owner_based():
    source = _source(SHELL)
    assert "class ListCtrlCoords(wx.ListCtrl):" in source
    assert 'self.InsertColumn(0, _(u"Type"))' in source
    assert 'self.InsertColumn(1, _(u"Coordonnée"))' in source
    assert "self.owner.IDcandidat" in source
    assert "class ListCtrlDiplomes(wx.ListCtrl):" in source
    assert "self.listeDiplomes" in source
    assert "self.GetParent().IDcandidat" not in source


def test_candidate_exposes_named_actions_instead_of_micro_buttons():
    source = _source(SHELL)
    for label in (
        "Ajouter",
        "Modifier",
        "Supprimer",
        "Modifier les qualifications…",
        "Référentiel des villes…",
        "Convertir en salarié…",
        "Courrier / email",
        "Valider",
        "Annuler",
    ):
        assert label in source
    assert "wx.WrapSizer" in source


def test_candidate_keeps_birthdate_city_and_embedded_recruitment_contracts():
    source = _source(SHELL)
    assert "CORE.TextCtrlCp" in source
    assert "CORE.TextCtrlVille" in source
    assert "self.OnRadioDateNaiss(None)" in source
    assert "self.ctrl_candidatures = CORE.OL_candidatures.ListView" in source
    assert "self.ctrl_entretiens = CORE.OL_entretiens.ListView" in source
    assert "DLG_Gestion_villes.Dialog" in source
