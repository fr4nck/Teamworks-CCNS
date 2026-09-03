from __future__ import annotations

import sys
import time

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtWidgets import QApplication, QTableView

from data_adapter import ContractView, PersonView
from frugality import FrugalityProbe
from models import ContractsTableModel, PeopleTableModel


PEOPLE_COUNT = 1000
CONTRACTS_PER_PERSON = 6


def build_people(count: int) -> tuple[PersonView, ...]:
    return tuple(
        PersonView(
            id=f"BENCH-{index:04d}",
            name=f"Personne {index:04d}",
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

    # Force la création/résolution du premier écran de données sans afficher
    # 1000 widgets : QTableView reste virtualisé et interroge le modèle à la demande.
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

    snapshot = probe.snapshot(direct_dependencies=2)
    print(
        "[Teamworks Qt benchmark] "
        f"people={PEOPLE_COUNT} · contracts/person={CONTRACTS_PER_PERSON} · "
        f"filtered_rows={proxy.rowCount()} · filter={filter_ms:.2f} ms · "
        f"contracts_reset={reset_ms:.2f} ms · {snapshot.compact()}"
    )

    people_view.close()
    contracts_view.close()


if __name__ == "__main__":
    main()
