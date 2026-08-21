import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS = (
    ("DLG_Config_affectations.py", "DLG_Config_affectations_core.py", "Affectations de recrutement", "cand_affectations"),
    ("DLG_Config_diffuseurs.py", "DLG_Config_diffuseurs_core.py", "Diffuseurs d'offres", "emplois_diffuseurs"),
)


def _path(name):
    return ROOT / "teamworks" / "Dlg" / name


def _src(name):
    return _path(name).read_text(encoding="utf-8")


def test_aux_references_are_valid_python():
    for shell, core, title, table in PAIRS:
        ast.parse(_src(shell))
        ast.parse(_src(core))


def test_aux_references_keep_business_rules_in_exact_cores():
    for shell, core, title, table in PAIRS:
        shell_source, core_source = _src(shell), _src(core)
        assert "class Panel(CORE.Panel):" in shell_source
        for method in ("Ajouter", "Modifier", "Supprimer"):
            assert "def %s" % method in core_source
        assert table in core_source


def test_aux_references_share_the_same_semantic_language():
    for shell, core, title, table in PAIRS:
        source = _src(shell)
        assert "CTRL_Section.Section(" in source
        assert title in source
        assert 'UTILS_Styles.ApplyWindowProfile(self, "standard")' in source
        assert 'texte=_(u"Ajouter")' in source
        assert 'texte=_(u"Modifier")' in source
        assert 'texte=_(u"Supprimer")' in source
        for legacy in ("wx.BitmapButton", "wx.FlexGridSizer", ".Fit(self)", "wx.ImageList", "#EEF4FB", "Images/16x16"):
            assert legacy not in source


def test_aux_references_show_usage_counts():
    affectations = _src("DLG_Config_affectations.py")
    diffuseurs = _src("DLG_Config_diffuseurs.py")
    assert "COUNT(cand_affectations.IDcand_affectation)" in affectations
    assert "COUNT(emplois_diffuseurs.IDemploi_diffuseur)" in diffuseurs
