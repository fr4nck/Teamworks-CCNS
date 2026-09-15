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

from data_adapter import ContractView  # noqa: E402
from models import ContractsTableModel  # noqa: E402
from production_read_adapter import TeamworksProductionReadAdapter  # noqa: E402
from domain.repositories.ccns_data import CcnsContratRecord  # noqa: E402


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
