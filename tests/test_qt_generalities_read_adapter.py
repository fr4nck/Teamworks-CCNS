from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

from domain.repositories.person_data import (  # noqa: E402
    PersonCoordinateRecord,
    PersonGeneralitiesRecord,
)
from production_read_adapter import TeamworksProductionReadAdapter  # noqa: E402


class PersonDetailsReader:
    def lire_generalites(self, person_id):
        assert person_id == 12
        return PersonGeneralitiesRecord(
            12,
            "Mme",
            "DUPONT",
            "MARTIN",
            "Alice",
            "1990-02-03",
            35000,
            "Rennes",
            "France",
            "Française",
            "1 rue du Stade\nBâtiment B",
            "3510",
            "Bais",
            "Mémo libre",
            "Salariée",
        )

    def lire_coordonnees(self, person_id):
        assert person_id == 12
        return [
            PersonCoordinateRecord(4, "Mobile", "06 12 34 56 78", "Portable pro"),
            PersonCoordinateRecord(5, "Email", "test@example.org", None),
        ]

    def close(self):
        pass


class IdleReader:
    def close(self):
        pass


def test_generalities_mapping_formats_historical_fields_without_nir() -> None:
    adapter = TeamworksProductionReadAdapter(
        person_reader=PersonDetailsReader(),
        contract_reader=IdleReader(),
        activity_reader=IdleReader(),
    )

    details = adapter.get_person_generalities(12)

    assert details is not None
    assert details.civility == "Mme"
    assert details.maiden_name == "MARTIN"
    assert details.last_name == "DUPONT"
    assert details.first_name == "Alice"
    assert details.birth_date == "03/02/1990"
    assert details.birth_country == "France"
    assert details.birth_postcode == "35000"
    assert details.nationality == "Française"
    assert details.social_situation == "Salariée"
    assert details.address == "1 rue du Stade\nBâtiment B"
    assert details.postcode == "03510"
    assert details.city == "Bais"
    assert details.memo == "Mémo libre"
    assert [(item.key, item.category, item.text, item.label) for item in details.coordinates] == [
        (4, "Mobile", "06 12 34 56 78", "Portable pro"),
        (5, "Email", "test@example.org", ""),
    ]
    assert not hasattr(details, "nir")


def test_generalities_missing_record_stays_absent() -> None:
    class MissingReader(PersonDetailsReader):
        def lire_generalites(self, person_id):
            return None

    adapter = TeamworksProductionReadAdapter(
        person_reader=MissingReader(),
        contract_reader=IdleReader(),
        activity_reader=IdleReader(),
    )

    assert adapter.get_person_generalities(12) is None
