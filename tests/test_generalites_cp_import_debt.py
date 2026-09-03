from pathlib import Path


GENERALITES = Path("teamworks/Ctrl/CTRL_Page_generalites.py")


def test_import_historique_des_cp_est_identifie_comme_zone_a_remplacer():
    source = GENERALITES.read_text(encoding="utf-8")
    load = source.split("def Importation", 1)[1].split("def _bitmap_drapeau", 1)[0]
    assert 'self.text_cp.SetValue("%05d" % cp_resid)' in load
    assert 'self.text_cp_naiss.SetValue("%05d" % cp_naiss)' in load
