from pathlib import Path


def test_vacation_import_no_longer_depends_on_organizer_coordinates():
    source = Path("teamworks/Dlg/DLG_Importation_vacances.py").read_text(
        encoding="utf-8"
    )

    # Le choix utilisateur A/B/C pilote désormais directement la source
    # officielle. Une fiche organisateur absente ne peut donc plus faire
    # planter l'import ni déclencher une détection 2015 par code postal.
    assert "def ImportationZone" not in source
    assert "SELECT cp, ville" not in source
    assert "RechercherZone" not in source
    assert "self.GetZone()" in source
    assert "charger_vacances(zone)" in source
