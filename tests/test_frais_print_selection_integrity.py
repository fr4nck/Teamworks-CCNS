from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPRESSION = ROOT / "teamworks" / "Dlg" / "DLG_Impression_frais.py"


def test_checking_a_trip_for_printing_never_writes_to_gadgets():
    source = IMPRESSION.read_text(encoding="utf-8")
    start = source.index("    def OnCheckItem(self, index, flag):")
    end = source.index("    def Importation(self):", start)
    handler = source[start:end]

    assert 'ReqMAJ("gadgets"' not in handler
    assert "GestionDB.DB()" not in handler
