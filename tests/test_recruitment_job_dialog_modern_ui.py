import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_emploi.py"
CORE = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_emploi_core.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_job_dialog_shell_and_core_are_valid_python():
    ast.parse(_source(SHELL))
    ast.parse(_source(CORE))


def test_job_dialog_keeps_persistence_engine_in_core():
    shell = _source(SHELL)
    core = _source(CORE)
    assert "from Dlg import DLG_Saisie_emploi_core as CORE" in shell
    assert "class Panel(CORE.Panel):" in shell
    assert "def Sauvegarde" in core
    for table in (
        "emplois",
        "emplois_dispo",
        "emplois_fonctions",
        "emplois_affectations",
        "emplois_diffuseurs",
    ):
        assert table in core


def test_job_dialog_uses_four_semantic_sections():
    source = _source(SHELL)
    assert source.count("CTRL_Section.Section(") == 4
    for title in ("Généralités", "Disponibilités", "Poste", "Diffusion de l'offre"):
        assert title in source
    assert "CTRL_Texte.Label" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "wide")' in source


def test_job_dialog_has_no_legacy_layout_or_micro_buttons():
    source = _source(SHELL)
    for legacy in (
        "wx.StaticBox",
        "wx.FlexGridSizer",
        "wx.BitmapButton",
        ".Fit(self)",
        'size=(20, 20)',
        'Images/16x16',
    ):
        assert legacy not in source
    assert "wx.WrapSizer" in source
    assert 'texte=_(u"Gérer…")' in source


def test_job_period_list_context_menu_is_textual():
    source = _source(SHELL)
    assert "class ListBoxDisponibilites(wx.ListBox):" in source
    assert '_(u"Ajouter une période")' in source
    assert '_(u"Modifier la période")' in source
    assert '_(u"Supprimer la période")' in source
    assert "SetBitmap" not in source


def test_job_dialog_keeps_management_and_validation_contract():
    shell = _source(SHELL)
    core = _source(CORE)
    for method in (
        "OnAjouterPeriode",
        "OnModifierPeriode",
        "OnSupprimerPeriode",
        "OnGestionFonctions",
        "OnGestionAffectations",
        "OnGestionDiffuseurs",
        "Onbouton_ok",
        "Importation",
    ):
        assert "def %s" % method in core
    assert "self.OnGestionFonctions" in shell
    assert "self.OnGestionAffectations" in shell
    assert "self.OnGestionDiffuseurs" in shell
