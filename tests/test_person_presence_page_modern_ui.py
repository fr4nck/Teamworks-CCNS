import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "teamworks" / "Ctrl" / "CTRL_Page_presences.py"


def _source():
    return PAGE.read_text(encoding="utf-8")


def test_person_presence_page_is_valid_python():
    ast.parse(_source())


def test_person_presence_page_uses_semantic_layout_and_actions():
    source = _source()
    assert "wx.StaticBox" not in source
    assert "wx.BitmapButton" not in source
    assert ".Fit(self)" not in source
    assert 'titre=_(u"Présences")' in source
    assert "CTRL_Bouton_image.CTRL" in source
    assert "wx.WrapSizer" in source
    assert "CTRL_Texte.BodySecondary" in source
    for label in (
        'texte=_(u"Ajouter")',
        'texte=_(u"Modifier")',
        'texte=_(u"Supprimer")',
        'texte=_(u"Imprimer")',
        'texte=_(u"Statistiques")',
        'texte=_(u"Appliquer un modèle")',
    ):
        assert label in source


def test_person_presence_table_uses_neutral_rows_and_flexible_columns():
    source = _source()
    assert "#EEF4FB" not in source
    assert "CreationImage" not in source
    assert "FormateCouleur" not in source
    assert "OnGetItemImage(self, item):\n        return -1" in source
    assert 'UTILS_Interface.GetToken("surface_container_low")' in source
    assert "UTILS_Colonnes.ColonnesFlexibles" in source
    assert "extensibles=(3, 4, 7)" in source
    assert "self.nbreColonnes = 8" in source


def test_person_presence_search_is_first_class_not_hidden_toggle():
    source = _source()
    assert "self.barreRecherche.Show(False)" not in source
    assert "bouton_recherche" not in source
    assert "class BarreRecherche(wx.SearchCtrl)" in source
    assert "self.owner.listCtrl.Rechercher(txtSearch)" in source
    assert "Aucune présence trouvée" in source


def test_person_presence_dialogs_use_modern_calendar_and_window_profiles():
    source = _source()
    assert source.count("CTRL_Calendrier_tw.Panel(") == 2
    assert source.count('UTILS_Styles.ApplyWindowProfile(self, "wide")') >= 3
    assert "SetSize((640, 330))" not in source
    assert "SetSize((720, 400))" not in source
    assert "SetSize((400, 320))" not in source
    assert 'UTILS_Styles.ApplyWindowProfile(dlg, "compact")' in source
    assert 'titre=_(u"Dates")' in source


def test_person_presence_business_entry_points_are_preserved():
    source = _source()
    for method in (
        "Ajouter",
        "Modifier",
        "Supprimer",
        "OnBoutonImprimer",
        "OnBoutonStats",
        "AppliquerModele",
        "MAJpanel",
        "Importation",
        "Rechercher",
    ):
        assert "def %s" % method in source
    assert "DLG_Saisie_presence.Dialog" in source
    assert "DLG_Impression_calendrier_annuel.MyDialog" in source
    assert "DLG_Statistiques.Dialog" in source
    assert "DLG_Application_modele.Panel" in source
