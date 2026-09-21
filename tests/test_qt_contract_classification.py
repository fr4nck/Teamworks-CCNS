from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from application.control.contract_classification import resolve_contract_classification
from domain.repositories.ccns_data import CcnsContratRecord


POC = Path(__file__).resolve().parents[1] / "poc" / "qt-theme"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

from production_read_adapter import TeamworksProductionReadAdapter  # noqa: E402


def _record(
    *,
    classification=None,
    convention_code=None,
    ccns_group=None,
    contract_id=417,
):
    return CcnsContratRecord(
        IDcontrat=contract_id,
        IDpersonne=12,
        date_debut="2026-09-01",
        date_fin="2999-01-01",
        salaire_base=None,
        temps_hebdo=35.0,
        prime_anciennete=None,
        prenom="Test",
        nom="Contrat",
        classification=classification,
        type_contrat="CDI",
        date_rupture=None,
        convention_code=convention_code,
        ccns_group=ccns_group,
    )


def test_classification_historique_reste_prioritaire() -> None:
    record = _record(
        classification="Classification historique",
        convention_code="CCNS",
        ccns_group="G5",
    )

    view = TeamworksProductionReadAdapter._contract_to_view(record)

    assert view.classification == "Classification historique"
    assert view.id_historique == 417


def test_contrat_ccns_moderne_resout_le_groupe_a_la_date_du_contrat() -> None:
    record = _record(
        classification=None,
        convention_code="CCNS",
        ccns_group="G3",
    )

    view = TeamworksProductionReadAdapter._contract_to_view(record)

    assert view.classification == "Groupe 3"


def test_contrat_cee_ne_devient_jamais_un_groupe_ccns() -> None:
    record = _record(
        classification=None,
        convention_code="CEE",
        ccns_group="G3",
    )

    view = TeamworksProductionReadAdapter._contract_to_view(record)

    assert view.classification == "—"


def test_groupe_ccns_inconnu_conserve_le_code_stocke() -> None:
    result = resolve_contract_classification(
        legacy_classification=None,
        convention_code="CCNS",
        ccns_group="G99",
        reference_date=date(2026, 9, 1),
    )

    assert result == "G99"
