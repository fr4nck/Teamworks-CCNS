import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_deplacement.py"


def _source():
    return DIALOG.read_text(encoding="utf-8")


def test_travel_entry_is_valid_python():
    ast.parse(_source())


def test_travel_entry_uses_semantic_sections_and_charter():
    source = _source()
    assert "wx.FlexGridSizer" not in source
    assert "wx.StaticBox" not in source
    assert ".Fit(self)" not in source
    assert "wx.Font(" not in source
    assert source.count("CTRL_Section.Section(") == 3
    assert 'titre=_(u"Généralités")' in source
    assert 'titre=_(u"Trajet")' in source
    assert 'titre=_(u"Remboursement")' in source
    assert "CTRL_Texte.DataLarge" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "wide")' in source
    assert 'UTILS_Styles.GetLayoutSpacing("field_gap")' in source
    assert 'texte=_(u"Rechercher")' in source


def test_travel_entry_has_no_historical_fixed_label_and_micro_button_geometry():
    source = _source()
    assert "size=(95, -1)" not in source
    assert "size=(55, -1)" not in source
    assert "size=(20, 20)" not in source
    assert 'SetMinSize((UTILS_Styles.Scale(82), -1))' in source
    assert 'SetMinSize((UTILS_Styles.Scale(100), -1))' in source


def test_travel_entry_keeps_city_autocomplete_and_distance_contract():
    source = _source()
    assert 'sqlite3.connect(Chemins.GetStaticPath("Databases/Villes.db3"))' in source
    assert 'cur.execute("SELECT ville, cp FROM villes")' in source
    assert "class TextCtrlCp" in source
    assert "class TextCtrlVille" in source
    assert "def MajDistance" in source
    assert "def CalcMontantRmbst" in source
    assert "self.dialog.MajDistance()" in source


def test_travel_entry_keeps_persistence_contract():
    source = _source()
    assert 'DB.ReqInsert("deplacements", listeDonnees)' in source
    assert 'DB.ReqMAJ("deplacements", listeDonnees, "IDdeplacement", self.IDdeplacement)' in source
    assert 'DB.ReqInsert("distances", listeDonnees)' in source
    assert 'DB.ReqMAJ("distances", listeDonnees, "IDdistance", distanceID)' in source
    assert "PersonReader()" in source
    import_people = source.split("def ImportationPersonnes", 1)[1].split("def ImportationDistances", 1)[0]
    assert "reader.close()" in import_people
    assert "DB.Close()" not in import_people
