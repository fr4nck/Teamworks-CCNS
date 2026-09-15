from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

POC = Path(__file__).resolve().parents[1] / "poc" / "qt-theme"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QStandardItemModel  # noqa: E402

from data_adapter import (  # noqa: E402
    ContractView,
    ReimbursementView,
    ScenarioView,
    TripView,
)
from individual_activity_presenter import _replace_rows  # noqa: E402
from models import ContractsTableModel  # noqa: E402
from production_read_adapter import TeamworksProductionReadAdapter  # noqa: E402
from domain.repositories.ccns_data import CcnsContratRecord  # noqa: E402
from domain.repositories.individual_activity_data import (  # noqa: E402
    ReimbursementRecord,
    ScenarioRecord,
    TripRecord,
)


class _NoopReader:
    def close(self) -> None:
        return None


class _ActivityReader(_NoopReader):
    def lire_scenarios_personne(self, person_id):
        return [ScenarioRecord(71, int(person_id), "Semaine", "Test", "2026-09-01", "2026-09-07")]

    def lire_deplacements_personne(self, person_id):
        return [TripRecord(81, "2026-09-02", "Réunion", "Le Rheu", "Rennes", 20, False, "0.55", 0)]

    def lire_remboursements_personne(self, person_id):
        return [ReimbursementRecord(91, "2026-09-03", "11.00", "81")]



def _adapter() -> TeamworksProductionReadAdapter:
    return TeamworksProductionReadAdapter(
        person_reader=_NoopReader(),
        contract_reader=_NoopReader(),
        activity_reader=_ActivityReader(),
    )


def test_production_contract_keeps_historical_id() -> None:
    record = CcnsContratRecord(
        IDcontrat=417,
        IDpersonne=12,
        date_debut="2026-09-01",
        date_fin="2999-01-01",
        salaire_base=None,
        temps_hebdo=21.0,
        prime_anciennete=None,
        prenom="Test",
        nom="Contrat",
        classification="G1",
        type_contrat="CDI",
        date_rupture=None,
    )

    view = TeamworksProductionReadAdapter._contract_to_view(record)

    assert view.id_historique == 417
    assert view.kind == "CDI"


def test_contract_identity_does_not_depend_on_display_column() -> None:
    view = ContractView(
        kind="CDD",
        start="01/09/2026",
        end="31/08/2027",
        classification="G1",
        duration="21 h",
        status="Actif",
        id_historique=917,
    )
    model = ContractsTableModel((view,))

    assert model.columnCount() > 1
    for column in range(model.columnCount()):
        index = model.index(0, column)
        payload = model.data(index, Qt.ItemDataRole.UserRole)
        assert payload is view
        assert payload.id_historique == 917


def test_production_activity_views_keep_historical_ids() -> None:
    adapter = _adapter()
    try:
        assert adapter.list_scenarios(12)[0].id_historique == 71
        assert adapter.list_trips(12)[0].id_historique == 81
        assert adapter.list_reimbursements(12)[0].id_historique == 91
    finally:
        adapter.close()


@pytest.mark.parametrize(
    "view, values, expected_id",
    [
        (ScenarioView("Semaine", "Du 01/09 au 07/09", "Test", id_historique=71), ("Semaine", "Du 01/09 au 07/09", "Test"), 71),
        (TripView("81", "02/09/2026", "Réunion", "Le Rheu -> Rennes", "20 Km", "0.55 €/km", "11.00 €", "", id_historique=81), ("81", "02/09/2026", "Réunion", "Le Rheu -> Rennes", "20 Km", "0.55 €/km", "11.00 €", ""), 81),
        (ReimbursementView("91", "03/09/2026", "11.00 €", "N° 81", id_historique=91), ("91", "03/09/2026", "11.00 €", "N° 81"), 91),
    ],
)
def test_activity_identity_is_hidden_outside_display_columns(view, values, expected_id) -> None:
    model = QStandardItemModel(0, len(values))
    _replace_rows(model, ((view, values),))

    assert model.columnCount() == len(values)
    for column in range(model.columnCount()):
        item = model.item(0, column)
        payload = item.data(Qt.ItemDataRole.UserRole)
        assert payload is view
        assert payload.id_historique == expected_id
