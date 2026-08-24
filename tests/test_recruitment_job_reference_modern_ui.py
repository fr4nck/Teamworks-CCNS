import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "teamworks" / "Dlg" / "DLG_Config_emplois.py"
CORE = ROOT / "teamworks" / "Dlg" / "DLG_Config_emplois_core.py"


def _src(path):
    return path.read_text(encoding="utf-8")


def test_job_reference_is_valid_python():
    ast.parse(_src(SHELL))
    ast.parse(_src(CORE))


def test_job_reference_keeps_business_rules_in_core():
    shell, core = _src(SHELL), _src(CORE)
    assert "DLG_Config_emplois_core as CORE" in shell
    assert "class Panel(CORE.Panel):" in shell
    for method in ("Ajouter", "Modifier", "Supprimer"):
        assert "def %s" % method in core
    for table in ("emplois", "emplois_dispo", "emplois_fonctions", "emplois_affectations", "emplois_diffuseurs"):
        assert table in core


def test_job_reference_uses_semantic_table_and_wide_profile():
    source = _src(SHELL)
    assert "CTRL_Section.Section(" in source
    assert 'titre=_(u"Offres d\'emploi")' in source
    assert 'self.InsertColumn(1, _(u"Intitulé"))' in source
    assert 'self.InsertColumn(2, _(u"Détail"))' in source
    assert 'self.InsertColumn(3, _(u"Candidatures"))' in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "wide")' in source
    for legacy in ("wx.BitmapButton", "wx.FlexGridSizer", ".Fit(self)", "wx.ImageList", "#EEF4FB", "Images/16x16"):
        assert legacy not in source


def test_job_reference_counts_linked_applications_by_job_id():
    source = _src(SHELL)
    assert "LEFT JOIN candidatures ON candidatures.IDemploi = emplois.IDemploi" in source
    assert "COUNT(candidatures.IDcandidature)" in source
    assert "GROUP BY emplois.IDemploi" in source


def test_job_reference_keeps_config_parent_contract():
    source = _src(SHELL)
    assert 'name="config_emploi"' in source
    assert "def MAJpanel" in _src(CORE)
