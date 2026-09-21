import json
from datetime import datetime
from decimal import Decimal

from domain.migration.expense_inventory import (
    RawReimbursementRow,
    RawTripRow,
    analyze_expense_pilot_source,
)
from domain.migration.inventory_model import ColumnDefinition, ColumnStats, DatabaseInventory, TableInventory
from domain.migration.migration_report import (
    READY_FOR_MIGRATION_ANALYSIS,
    REVIEW_REQUIRED,
    build_migration_inventory_report,
    render_markdown,
    to_json_dict,
)


def _clean_database() -> DatabaseInventory:
    id_column = ColumnDefinition(name="IDdeplacement", declared_type="INTEGER", nullable=False, is_primary_key=True)
    table = TableInventory(
        name="deplacements",
        row_count=1,
        primary_key_columns=("IDdeplacement",),
        columns=(ColumnStats(column=id_column, row_count=1, distinct_count=1),),
    )
    return DatabaseInventory(
        engine="sqlite",
        engine_version="3.45.0",
        source_label="snapshot-test.sqlite",
        inventoried_at=datetime(2026, 9, 21, 10, 0, 0),
        table_count=1,
        total_row_count=1,
        tables=(table,),
    )


def _table_without_primary_key() -> TableInventory:
    column = ColumnDefinition(name="distance", declared_type="REAL", nullable=True)
    return TableInventory(
        name="distances",
        row_count=3,
        primary_key_columns=(),
        columns=(ColumnStats(column=column, row_count=3),),
    )


def test_clean_database_with_no_expense_data_is_ready():
    report = build_migration_inventory_report(_clean_database())

    assert report.decision == READY_FOR_MIGRATION_ANALYSIS
    assert report.blocking_findings == ()


def test_table_without_primary_key_is_review_not_blocking():
    base = _clean_database()
    database = DatabaseInventory(
        engine=base.engine,
        engine_version=base.engine_version,
        source_label=base.source_label,
        inventoried_at=base.inventoried_at,
        table_count=base.table_count + 1,
        total_row_count=base.total_row_count,
        tables=base.tables + (_table_without_primary_key(),),
    )

    report = build_migration_inventory_report(database)

    assert report.decision == READY_FOR_MIGRATION_ANALYSIS
    codes = {f.code for f in report.review_findings}
    assert "TABLE_PRIMARY_KEY_UNKNOWN" in codes


def test_duplicate_primary_key_is_blocking_and_flips_decision():
    id_column = ColumnDefinition(name="IDdeplacement", declared_type="INTEGER", nullable=False, is_primary_key=True)
    table = TableInventory(
        name="deplacements",
        row_count=2,
        primary_key_columns=("IDdeplacement",),
        columns=(ColumnStats(column=id_column, row_count=2, distinct_count=1),),
        duplicate_key_row_count=1,
    )
    database = DatabaseInventory(
        engine="sqlite",
        engine_version="3.45.0",
        source_label="snapshot-test.sqlite",
        inventoried_at=datetime(2026, 9, 21, 10, 0, 0),
        table_count=1,
        total_row_count=2,
        tables=(table,),
    )

    report = build_migration_inventory_report(database)

    assert report.decision == REVIEW_REQUIRED
    codes = {f.code for f in report.blocking_findings}
    assert "TABLE_PRIMARY_KEY_DUPLICATED" in codes


def test_expense_blocking_finding_flips_decision():
    expense = analyze_expense_pilot_source(
        source_people_ids=[], trips=[], reimbursements=[
            RawReimbursementRow(
                reimbursement_id=1,
                person_id=99,
                payment_date="2026-01-01",
                amount=Decimal("10"),
                legacy_trip_list="",
            )
        ],
    )

    report = build_migration_inventory_report(_clean_database(), expense=expense)

    assert report.decision == REVIEW_REQUIRED
    assert any(f.code == "REIMBURSEMENT_PERSON_NOT_FOUND" for f in report.blocking_findings)


def test_json_dict_is_serializable_and_deterministic():
    expense = analyze_expense_pilot_source(
        source_people_ids=[12],
        trips=[
            RawTripRow(
                trip_id=7,
                person_id=12,
                travel_date="2026-09-10",
                departure_postcode="03510",
                arrival_postcode="35000",
                distance=Decimal("20"),
                tariff_per_km=Decimal("0.5"),
                round_trip=0,
                reimbursement_id=3,
            )
        ],
        reimbursements=[
            RawReimbursementRow(
                reimbursement_id=3,
                person_id=12,
                payment_date="2026-09-30",
                amount=Decimal("10"),
                legacy_trip_list="7",
            )
        ],
    )
    report = build_migration_inventory_report(_clean_database(), expense=expense)

    payload = to_json_dict(report)
    encoded = json.dumps(payload, ensure_ascii=False)
    decoded = json.loads(encoded)

    assert decoded["decision"] == READY_FOR_MIGRATION_ANALYSIS
    assert decoded["expense_pilot"]["trip_count"] == 1
    assert decoded["expense_pilot"]["mirror_audits"][0]["matches"] is True

    second_payload = to_json_dict(build_migration_inventory_report(_clean_database(), expense=expense))
    assert payload == second_payload


def test_markdown_report_contains_summary_and_decision():
    report = build_migration_inventory_report(_clean_database())

    markdown = render_markdown(report)

    assert "Base inspectée : snapshot-test.sqlite" in markdown
    assert "Moteur : sqlite 3.45.0" in markdown
    assert "Décision automatique :" in markdown
    assert READY_FOR_MIGRATION_ANALYSIS in markdown


def test_markdown_report_lists_blocking_findings_by_code():
    id_column = ColumnDefinition(name="IDdeplacement", declared_type="INTEGER", nullable=False, is_primary_key=True)
    table = TableInventory(
        name="deplacements",
        row_count=2,
        primary_key_columns=("IDdeplacement",),
        columns=(ColumnStats(column=id_column, row_count=2, distinct_count=1),),
        duplicate_key_row_count=1,
    )
    database = DatabaseInventory(
        engine="sqlite",
        engine_version="3.45.0",
        source_label="snapshot-test.sqlite",
        inventoried_at=datetime(2026, 9, 21, 10, 0, 0),
        table_count=1,
        total_row_count=2,
        tables=(table,),
    )

    markdown = render_markdown(build_migration_inventory_report(database))

    assert "TABLE_PRIMARY_KEY_DUPLICATED" in markdown
    assert REVIEW_REQUIRED in markdown


def test_markdown_is_deterministic_excluding_timestamp_field():
    report_a = build_migration_inventory_report(_clean_database())
    report_b = build_migration_inventory_report(_clean_database())

    assert render_markdown(report_a) == render_markdown(report_b)
