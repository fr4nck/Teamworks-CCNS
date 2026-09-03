from __future__ import annotations

import sys
import time
from datetime import date
from decimal import Decimal

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtWidgets import QApplication, QTableView

from data_adapter import ContractView, PersonView
from domain.contracts.contract import Contract
from domain.contracts.contract_type import ContractType
from domain_read_adapter import DomainPeopleReadAdapter
from frugality import FrugalityProbe
from infrastructure.repositories.contracts_repository import ContractRepository
from infrastructure.repositories.people_repository import PeopleRepository
from models import ContractsTableModel, PeopleTableModel


PEOPLE_COUNT = 1000
CONTRACTS_PER_PERSON = 6
DOMAIN_CONTRACT_COUNT = 6000


def build_people(count: int) -> tuple[PersonView, ...]:
    return tuple(
        PersonView(
            id=f"BENCH-{index:04d}",
            id_historique=None,
            name=f"Personne {index:04d}",
            birth_date="",
            role="",
            classification="",
            contract="",
            weekly_hours="",
            status="Actif" if index % 5 else "Inactif",
            site="",
            medical="",
            mutual="",
        )
        for index in range(count)
    )


def build_contracts(count: int) -> tuple[ContractView, ...]:
    return tuple(
        ContractView(
            kind="Contrat test",
            start="01/09/2026",
            end="31/08/2027",
            classification="",
            duration="",
            status="Lecture seule",
        )
        for _ in range(count)
    )


def build_domain_contracts(count: int, person_id: str) -> tuple[Contract, ...]:
    """Construit une charge domaine variée sans contourner les invariants Contract."""
    return tuple(
        Contract(
            person_id=person_id,
            contract_type=ContractType.CDI,
            start_date=date(2026, 9, 1),
            end_date=None if index % 2 == 0 else date(2027, 8, 31),
            weekly_hours=Decimal("35.00") if index % 3 == 0 else None,
            weekly_reference_hours=None if index % 3 == 0 else 35.0,
            ccns_classification_code="Groupe 3",
            contract_status="draft",
        )
        for index in range(count)
    )


def benchmark_domain_adaptation() -> tuple[float, float, int]:
    """Mesure séparément mapping pur puis repository + adaptation, sans Qt."""
    person_id = "BENCH-DOMAIN"
    contracts = build_domain_contracts(DOMAIN_CONTRACT_COUNT, person_id)

    mapping_started = time.perf_counter()
    mapped = tuple(DomainPeopleReadAdapter._contract_to_view(item) for item in contracts)
    mapping_ms = (time.perf_counter() - mapping_started) * 1000.0

    contracts_repo = ContractRepository()
    contracts_repo.replace_all(contracts)
    adapter = DomainPeopleReadAdapter(PeopleRepository(), contracts_repo)

    adapter_started = time.perf_counter()
    through_adapter = adapter.list_contracts(person_id)
    adapter_ms = (time.perf_counter() - adapter_started) * 1000.0

    assert any(item.end == "—" for item in mapped)
    assert any(item.end != "—" for item in mapped)
    assert len(through_adapter) == DOMAIN_CONTRACT_COUNT

    return mapping_ms, adapter_ms, len(through_adapter)


def main() -> None:
    started_at = time.perf_counter()
    app = QApplication(sys.argv)

    probe = FrugalityProbe(started_at=started_at)
    people = build_people(PEOPLE_COUNT)
    contracts = build_contracts(CONTRACTS_PER_PERSON)

    people_model = PeopleTableModel(people)
    proxy = QSortFilterProxyModel()
    proxy.setSourceModel(people_model)
    proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    proxy.setFilterKeyColumn(-1)

    contracts_model = ContractsTableModel()
    contracts_model.replace(contracts)

    people_view = QTableView()
    people_view.setModel(proxy)
    contracts_view = QTableView()
    contracts_view.setModel(contracts_model)

    people_view.resize(1100, 650)
    contracts_view.resize(900, 320)
    people_view.show()
    contracts_view.show()
    app.processEvents()

    search_started = time.perf_counter()
    proxy.setFilterFixedString("Personne 09")
    app.processEvents()
    filter_ms = (time.perf_counter() - search_started) * 1000.0

    reset_started = time.perf_counter()
    contracts_model.replace(build_contracts(CONTRACTS_PER_PERSON + 2))
    app.processEvents()
    reset_ms = (time.perf_counter() - reset_started) * 1000.0

    mapping_ms, adapter_ms, adapted_count = benchmark_domain_adaptation()
    mapping_unit_ms = mapping_ms / DOMAIN_CONTRACT_COUNT
    adapter_unit_ms = adapter_ms / DOMAIN_CONTRACT_COUNT

    snapshot = probe.snapshot(direct_dependencies=2)
    print(
        "[Teamworks Qt benchmark] "
        f"people={PEOPLE_COUNT} · contracts/person={CONTRACTS_PER_PERSON} · "
        f"filtered_rows={proxy.rowCount()} · filter={filter_ms:.2f} ms · "
        f"contracts_reset={reset_ms:.2f} ms · {snapshot.compact()}"
    )
    print(
        "[Teamworks Domain benchmark] "
        f"contracts={adapted_count} · mapping={mapping_ms:.2f} ms "
        f"({mapping_unit_ms:.4f} ms/contrat) · "
        f"repository+adapter={adapter_ms:.2f} ms "
        f"({adapter_unit_ms:.4f} ms/contrat)"
    )

    people_view.close()
    contracts_view.close()


if __name__ == "__main__":
    main()
