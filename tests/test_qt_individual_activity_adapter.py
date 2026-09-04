from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

from domain.repositories.individual_activity_data import (  # noqa: E402
    ReimbursementRecord,
    ScenarioRecord,
    TripRecord,
)
from production_read_adapter import TeamworksProductionReadAdapter  # noqa: E402


class IdleReader:
    def close(self):
        pass


class ActivityReader:
    def lire_scenarios_personne(self, person_id):
        assert person_id == 12
        return [ScenarioRecord(7, 12, "Saison", None, "2026-09-01", "2027-06-30")]

    def lire_deplacements_personne(self, person_id):
        assert person_id == 12
        return [
            TripRecord(8, "2026-09-03", "Réunion", "Bais", "Vitré", 123, "True", "0.55", 4),
            TripRecord(9, "2026-09-04", None, "Bais", "Moutiers", "", "False", None, 0),
        ]

    def lire_remboursements_personne(self, person_id):
        assert person_id == 12
        return [
            ReimbursementRecord(4, "2026-09-30", "67.65", "8-9"),
            ReimbursementRecord(5, "2026-10-31", 0, ""),
        ]

    def close(self):
        pass


def _adapter():
    return TeamworksProductionReadAdapter(
        person_reader=IdleReader(),
        contract_reader=IdleReader(),
        activity_reader=ActivityReader(),
    )


def test_scenario_mapping_matches_historical_individual_list() -> None:
    views = _adapter().list_scenarios(12)
    assert views[0].name == "Saison"
    assert views[0].period == "Du 01/09/2026 au 30/06/2027"
    assert views[0].description == "Aucune description"


def test_trip_mapping_is_decimal_safe_and_keeps_historical_route_semantics() -> None:
    views = _adapter().list_trips(12)
    assert views[0].number == "8"
    assert views[0].date == "03/09/2026"
    assert views[0].route == "Bais <--> Vitré"
    assert views[0].distance == "123 Km"
    assert views[0].tariff == "0.55 €/km"
    assert views[0].amount == "67.65 €"
    assert views[0].reimbursement == "N°4"
    assert views[1].amount == "—"
    assert views[1].reimbursement == ""


def test_reimbursement_mapping_preserves_legacy_textual_attachment_display() -> None:
    views = _adapter().list_reimbursements(12)
    assert views[0].number == "4"
    assert views[0].date == "30/09/2026"
    assert views[0].amount == "67.65 €"
    assert views[0].attached_trips == "N° 8, 9"
    assert views[1].attached_trips == "Aucun déplacement rattaché"
