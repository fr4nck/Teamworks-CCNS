from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
QT_POC = ROOT / "poc" / "qt-theme"
if str(QT_POC) not in sys.path:
    sys.path.insert(0, str(QT_POC))

from production_read_adapter import TeamworksProductionReadAdapter


def _contract(*, date_fin):
    return SimpleNamespace(
        type_contrat="CDI",
        date_debut="2020-09-01",
        date_fin=date_fin,
        classification="Groupe 4",
        temps_hebdo=35.0,
    )


def test_contract_projection_translates_historical_indefinite_end_date():
    view = TeamworksProductionReadAdapter._contract_to_view(
        _contract(date_fin="2999-01-01")
    )

    assert view.start == "01/09/2020"
    assert view.end == "Indétermin."


def test_contract_projection_keeps_real_fixed_end_date():
    view = TeamworksProductionReadAdapter._contract_to_view(
        _contract(date_fin="2026-12-31")
    )

    assert view.end == "31/12/2026"
