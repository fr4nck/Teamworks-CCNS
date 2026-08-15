from pathlib import Path


def test_vacation_zone_lookup_handles_missing_organizer():
    source = Path("teamworks/Dlg/DLG_Importation_vacances.py").read_text(encoding="utf-8")

    assert "resultats = DB.ResultatReq()" in source
    assert "if not resultats:" in source
    assert "Organisateur introuvable" in source
    assert "cp, ville = resultats[0]" in source
    assert "DB.ResultatReq()[0]" not in source

    close_pos = source.index("DB.Close()", source.index("def ImportationZone"))
    guard_pos = source.index("if not resultats:", source.index("def ImportationZone"))
    assert close_pos < guard_pos
