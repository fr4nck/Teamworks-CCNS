import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "teamworks" / "Ctrl" / "CTRL_Page_generalites.py"


def _source():
    return PAGE.read_text(encoding="utf-8")


def test_generalities_is_valid_python():
    ast.parse(_source())


def test_generalities_uses_five_semantic_sections_without_legacy_frames():
    source = _source()
    page = source.split("class TestPopup", 1)[0]
    assert source.count("CTRL_Section.Section(") == 5
    for title in (
        'titre=_(u"Identité")',
        'titre=_(u"Situation sociale")',
        'titre=_(u"Adresse")',
        'titre=_(u"Coordonnées")',
        'titre=_(u"Mémo")',
    ):
        assert title in source
    assert "wx.FlexGridSizer" not in page
    assert "wx.StaticBox" not in page
    assert "wx.StaticBoxSizer" not in page
    assert "wx.BitmapButton" not in page
    assert ".Fit(self)" not in page
    assert 'UTILS_Interface.GetToken("surface")' in source
    assert 'UTILS_Styles.GetLayoutSpacing("page_gap")' in source


def test_generalities_security_number_status_is_semantic_text_not_micro_icon():
    source = _source()
    assert "CTRL_Texte.Caption" in source
    assert 'SetLabel(_(u"À vérifier"))' in source
    assert 'GetToken("danger")' in source
    assert 'SetLabel(_(u"Non renseigné"))' in source
    assert 'GetToken("on_surface_variant")' in source
    assert 'SetLabel(_(u"Valide"))' in source
    assert 'GetToken("success")' in source
    assert '"Images/16x16/Interdit.png"' not in source
    assert '"Images/16x16/Ok.png"' not in source


def test_generalities_keeps_country_flags_as_business_content():
    source = _source()
    assert "def _bitmap_drapeau" in source
    assert '"Images/Drapeaux/%s.png"' in source
    assert "wx.IMAGE_QUALITY_HIGH" in source
    assert "SetPaysNaiss" in source
    assert "SetNationalite" in source


def test_generalities_keeps_autocomplete_persistence_and_header_contract():
    source = _source()
    assert 'sqlite3.connect(Chemins.GetStaticPath("Databases/Villes.db3"))' in source
    assert "def Code_KillFocus1" in source
    assert "def VilleText1" in source
    assert "def Code_KillFocus2" in source
    assert "def VilleText2" in source
    assert 'DB.ReqInsert("personnes", listeDonnees)' in source
    assert 'DB.ReqMAJ(\n                "personnes", listeDonnees, "IDpersonne", self.IDpersonne' in source
    assert "MaJ_NomPrenom_Fiche" in source
    assert "MaJ_Adresse_Fiche" in source
    assert "MaJ_DateNaiss_Fiche" in source


def test_generalities_coordinates_are_responsive_and_use_labeled_actions():
    source = _source()
    assert "class ListCtrlCoords" in source
    assert "def _ajuster_colonne" in source
    assert "wx.BORDER_NONE" in source
    assert 'texte=_(u"Ajouter")' in source
    assert 'texte=_(u"Modifier")' in source
    assert 'texte=_(u"Supprimer")' in source
    assert 'texte=_(u"Rechercher")' in source
    assert '"PINK"' not in source
    assert "wx.Colour(" not in source
