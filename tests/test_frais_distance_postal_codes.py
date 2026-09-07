from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_deplacement.py"
TABLES = ROOT / "teamworks" / "Data" / "DATA_Tables.py"


def test_distance_cache_keeps_postal_codes_as_text():
    source = DIALOG.read_text(encoding="utf-8")
    start = source.index("    def SauvegardeDistance(self):")
    end = source.index("\n\nclass AdvancedComboBox", start)
    method = source[start:end]

    assert "cp_depart = self.ctrl_cp_depart.GetValue()" in method
    assert "cp_arrivee = self.ctrl_cp_arrivee.GetValue()" in method
    assert "int(self.ctrl_cp_depart.GetValue())" not in method
    assert "int(self.ctrl_cp_arrivee.GetValue())" not in method


def test_distance_schema_stores_postal_codes_as_varchar_5():
    source = TABLES.read_text(encoding="utf-8")
    start = source.index('    "distances":')
    end = source.index('    "deplacements":', start)
    table = source[start:end]

    assert '("cp_depart", "VARCHAR(5)"' in table
    assert '("cp_arrivee", "VARCHAR(5)"' in table
