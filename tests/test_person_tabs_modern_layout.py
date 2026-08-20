import ast
from pathlib import Path


SCENARIOS = Path("teamworks/Ctrl/CTRL_Page_scenarios.py")
QUESTIONNAIRE = Path("teamworks/Ctrl/CTRL_Page_questionnaire.py")
CANDIDATURES = Path("teamworks/Ctrl/CTRL_Page_candidatures.py")


def _source(path):
    return path.read_text(encoding="utf-8")


def test_modern_person_tabs_are_valid_python():
    for path in (SCENARIOS, QUESTIONNAIRE, CANDIDATURES):
        ast.parse(_source(path))


def test_scenarios_page_is_simple_and_expansive():
    source = _source(SCENARIOS)
    assert "FlexGridSizer" not in source
    assert "StaticBoxSizer" not in source
    assert ".Fit(self)" not in source
    assert "wx.BoxSizer" in source
    assert 'GetToken("surface")' in source


def test_questionnaire_uses_available_width_instead_of_335_pixels():
    source = _source(QUESTIONNAIRE)
    assert "FlexGridSizer" not in source
    assert "largeurReponse=335" not in source
    assert "AjusterLargeurs" in source
    assert "largeur * 0.38" in source
    assert "SetColumnWidth(0, largeur_question)" in source
    assert "SetColumnWidth(1, largeur_reponse)" in source
    assert "track.largeur = largeur_ctrl" in source
    assert "CalculatePositions" in source


def test_recruitment_page_uses_labeled_actions_and_no_vertical_button_grids():
    source = _source(CANDIDATURES)
    assert "FlexGridSizer" not in source
    assert "StaticBoxSizer" not in source
    assert ".Fit(self)" not in source
    assert "wx.WrapSizer" in source
    assert "CTRL_Bouton_image.CTRL" in source
    assert 'texte=label' in source
    assert '_(u"Ajouter")' in source
    assert '_(u"Modifier")' in source
    assert '_(u"Supprimer")' in source
