import sqlite3

import pytest

from domain.migration.expense_inventory import analyze_expense_pilot_source
from domain.migration.expense_inventory_loader import (
    load_expense_pilot_person_ids,
    load_expense_pilot_reimbursements,
    load_expense_pilot_trips,
)
from domain.migration.inventory_engine import build_database_inventory
from domain.migration.migration_report import (
    READY_FOR_MIGRATION_ANALYSIS,
    REVIEW_REQUIRED,
    build_migration_inventory_report,
    render_markdown,
    to_json_dict,
)
from infrastructure.persistence.legacy_sqlite_inventory_adapter import SqliteLegacyDatabasePort


def _schema() -> str:
    return """
        CREATE TABLE personnes (
            IDpersonne INTEGER PRIMARY KEY AUTOINCREMENT,
            nom VARCHAR(100),
            prenom VARCHAR(100)
        );
        CREATE TABLE deplacements (
            IDdeplacement INTEGER PRIMARY KEY AUTOINCREMENT,
            IDpersonne INTEGER,
            date DATE,
            objet VARCHAR(100),
            cp_depart VARCHAR(5),
            ville_depart VARCHAR(200),
            cp_arrivee VARCHAR(5),
            ville_arrivee VARCHAR(200),
            distance FLOAT,
            aller_retour VARCHAR(5),
            tarif_km FLOAT,
            IDremboursement INTEGER
        );
        CREATE TABLE remboursements (
            IDremboursement INTEGER PRIMARY KEY AUTOINCREMENT,
            IDpersonne INTEGER,
            date DATE,
            montant FLOAT,
            listeIDdeplacement VARCHAR(300)
        );
        CREATE TABLE distances (
            IDdistance INTEGER PRIMARY KEY AUTOINCREMENT,
            cp_depart VARCHAR(5),
            ville_depart VARCHAR(200),
            cp_arrivee VARCHAR(5),
            ville_arrivee VARCHAR(200),
            distance FLOAT
        );
    """


def _clean_dataset_path(tmp_path):
    path = tmp_path / "clean.sqlite"
    connection = sqlite3.connect(str(path))
    connection.executescript(_schema())
    connection.executescript(
        """
        INSERT INTO personnes VALUES (12, 'Dupont', 'Alice');
        INSERT INTO deplacements VALUES
            (7, 12, '2026-09-10', 'Réunion', '03510', 'BRUZ', '35000', 'RENNES', 20.0, '0', 0.5, 3);
        INSERT INTO remboursements VALUES (3, 12, '2026-09-30', 10.00, '7');
        INSERT INTO distances VALUES (1, '03510', 'BRUZ', '35000', 'RENNES', 20.0);
        """
    )
    connection.commit()
    connection.close()
    return path


def _broken_dataset_path(tmp_path):
    path = tmp_path / "broken.sqlite"
    connection = sqlite3.connect(str(path))
    connection.executescript(_schema())
    connection.executescript(
        """
        INSERT INTO personnes VALUES (12, 'Dupont', 'Alice');
        -- rattaché à un remboursement inexistant
        INSERT INTO deplacements VALUES
            (7, 12, '2026-09-10', 'Réunion', '03510', 'BRUZ', '35000', 'RENNES', 20.0, '0', 0.5, 99);
        """
    )
    connection.commit()
    connection.close()
    return path


def _run(path):
    with SqliteLegacyDatabasePort.from_path(path) as port:
        database = build_database_inventory(port)
        expense = analyze_expense_pilot_source(
            source_people_ids=load_expense_pilot_person_ids(port),
            trips=load_expense_pilot_trips(port),
            reimbursements=load_expense_pilot_reimbursements(port),
        )
    return build_migration_inventory_report(database, expense=expense)


def test_clean_dataset_is_ready_for_migration_analysis(tmp_path):
    report = _run(_clean_dataset_path(tmp_path))

    assert report.decision == READY_FOR_MIGRATION_ANALYSIS
    assert report.blocking_findings == ()
    assert report.expense.summary.trip_count == 1
    assert report.expense.summary.reimbursement_count == 1
    assert report.expense.mirror_audits[0].matches is True


def test_broken_dataset_requires_review(tmp_path):
    report = _run(_broken_dataset_path(tmp_path))

    assert report.decision == REVIEW_REQUIRED
    codes = {f.code for f in report.blocking_findings}
    assert "TRIP_REIMBURSEMENT_NOT_FOUND" in codes


def test_json_and_markdown_are_generated_for_clean_dataset(tmp_path):
    report = _run(_clean_dataset_path(tmp_path))

    payload = to_json_dict(report)
    markdown = render_markdown(report)

    assert payload["decision"] == READY_FOR_MIGRATION_ANALYSIS
    assert "distances" in {t["name"] for t in payload["database"]["tables"]}
    assert "Base inspectée" in markdown
    assert READY_FOR_MIGRATION_ANALYSIS in markdown


def test_same_snapshot_produces_the_same_report_excluding_timestamp(tmp_path):
    path = _clean_dataset_path(tmp_path)

    first = to_json_dict(_run(path))
    second = to_json_dict(_run(path))

    first["database"].pop("inventoried_at")
    second["database"].pop("inventoried_at")
    assert first == second


def test_personal_data_is_never_sampled_in_the_report(tmp_path):
    report = _run(_clean_dataset_path(tmp_path))

    payload = to_json_dict(report)
    personnes = next(t for t in payload["database"]["tables"] if t["name"] == "personnes")
    for column in personnes["columns"]:
        if column["name"] in ("nom", "prenom"):
            assert column["sample_values"] == []
