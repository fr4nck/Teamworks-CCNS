import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_candidature.py"
CORE = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_candidature_core.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_application_shell_and_core_are_valid_python():
    ast.parse(_source(SHELL))
    ast.parse(_source(CORE))


def test_application_keeps_persistence_engine_in_core():
    shell = _source(SHELL)
    core = _source(CORE)
    assert "from Dlg import DLG_Saisie_candidature_core as CORE" in shell
    assert "class Panel(CORE.Panel):" in shell
    assert "def Sauvegarde" in core
    for table in ("candidatures", "disponibilites", "cand_fonctions", "cand_affectations"):
        assert table in core


def test_application_uses_five_semantic_sections():
    source = _source(SHELL)
    assert source.count("CTRL_Section.Section(") == 5
    for title in ("Dépôt de candidature", "Offre d'emploi", "Disponibilités", "Poste souhaité", "Réponse"):
        assert title in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "workspace")' in source


def test_application_has_no_legacy_chrome():
    source = _source(SHELL)
    for legacy in (
        "wx.StaticBox",
        "wx.FlexGridSizer",
        "wx.BitmapButton",
        ".Fit(self)",
        "BitmapComboBox",
        "Images/16x16",
        'size=(20, 20)',
    ):
        assert legacy not in source
    assert "wx.WrapSizer" in source


def test_application_keeps_business_indexes_as_text_choices():
    source = _source(SHELL)
    assert "DEPOT_TYPES = (" in source
    assert "DECISIONS = (" in source
    assert "REPONSE_TYPES = (" in source
    assert "self.ctrl_type.GetSelection()" in _source(CORE)
    assert "self.ctrl_decision.GetSelection()" in _source(CORE)
    assert "self.ctrl_type_reponse.GetSelection()" in _source(CORE)


def test_application_offer_choice_uses_explicit_owner_not_parent_depth():
    source = _source(SHELL)
    assert "class ChoiceEmploi(wx.Choice):" in source
    assert "self.owner = owner" in source
    assert "self.owner.listeDisponibilites" in source
    assert "self.owner.ctrl_fonction.CocheListe" in source
    assert "self.owner.ctrl_affectations.CocheListe" in source
    assert "self.GetParent().listeDisponibilites" not in source


def test_application_keeps_management_and_response_contract():
    core = _source(CORE)
    for method in (
        "OnAjouterPeriode",
        "OnModifierPeriode",
        "OnSupprimerPeriode",
        "OnGestionEmplois",
        "OnGestionFonctions",
        "OnGestionAffectations",
        "OnCheckReponse",
        "OnCheckReponseCommuniquee",
        "Onbouton_courrier",
        "Onbouton_ok",
    ):
        assert "def %s" % method in core
