from __future__ import annotations

import pytest

from infrastructure.persistence.individual_activity_reader import IndividualActivityReader


class FakeDb:
    def __init__(self, responses):
        self.responses = list(responses)
        self.queries = []
        self.closed = False

    def ExecuterReq(self, req):
        self.queries.append(req)

    def ResultatReq(self):
        return self.responses.pop(0)

    def Close(self):
        self.closed = True


def test_reader_maps_historical_scenarios_and_expenses() -> None:
    db = FakeDb(
        [
            [(7, 12, "Saison", None, "2026-09-01", "2027-06-30")],
            [(8, "2026-09-03", "Réunion", "Bais", "Vitré", 123, "True", 0.55, 4)],
            [(4, "2026-09-30", 67.65, "8-9")],
        ]
    )
    reader = IndividualActivityReader(db_factory=lambda: db)

    scenarios = reader.lire_scenarios_personne(12)
    trips = reader.lire_deplacements_personne(12)
    reimbursements = reader.lire_remboursements_personne(12)

    assert scenarios[0].IDscenario == 7
    assert scenarios[0].nom == "Saison"
    assert trips[0].IDdeplacement == 8
    assert trips[0].IDremboursement == 4
    assert reimbursements[0].listeIDdeplacement == "8-9"
    assert all("IDpersonne=12" in query for query in db.queries)
    assert "ORDER BY date_debut DESC" in db.queries[0]
    assert "ORDER BY date;" in db.queries[1]
    assert "ORDER BY date;" in db.queries[2]

    reader.close()
    assert db.closed is True


@pytest.mark.parametrize("value", [None, 0, -1, True, "abc"])
def test_reader_rejects_invalid_person_ids(value) -> None:
    reader = IndividualActivityReader(db_factory=lambda: FakeDb([]))
    with pytest.raises(ValueError):
        reader.lire_scenarios_personne(value)
