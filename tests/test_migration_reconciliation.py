from domain.migration.reconciliation import (
    MigrationDisposition,
    MigrationLedgerEntry,
    ReconciliationMetric,
    ReconciliationReport,
)


def _entry(source_id, disposition=MigrationDisposition.MIGRATED, **changes):
    values = dict(
        source_system="noethys",
        source_table="personnes",
        source_id=str(source_id),
        disposition=disposition,
        destination_type="person",
        destination_id=f"p-{source_id}",
        reason_code=None,
    )
    values.update(changes)
    return MigrationLedgerEntry(**values)


def test_valid_report_requires_every_source_row_to_be_explained():
    report = ReconciliationReport.build(
        expected_source_rows=2,
        entries=[_entry(1), _entry(2)],
    )

    assert report.unexplained_rows == 0
    assert report.is_valid is True


def test_missing_source_row_blocks_validation():
    report = ReconciliationReport.build(
        expected_source_rows=2,
        entries=[_entry(1)],
    )

    assert report.unexplained_rows == 1
    assert report.is_valid is False
    assert "comptage source non réconcilié" in report.blocking_reasons()[0]


def test_transformed_ignored_and_rejected_require_reason_code():
    for disposition in (
        MigrationDisposition.TRANSFORMED,
        MigrationDisposition.IGNORED,
        MigrationDisposition.REJECTED,
    ):
        entry = _entry(1, disposition=disposition, reason_code=None)
        assert any("reason_code obligatoire" in error for error in entry.validate())


def test_ignored_row_can_be_explained_when_justified():
    entry = MigrationLedgerEntry(
        source_system="noethys",
        source_table="distances_cache",
        source_id="42",
        disposition=MigrationDisposition.IGNORED,
        reason_code="CACHE_RECALCULABLE",
        message="Cache technique reconstruit par le nouveau moteur.",
    )
    report = ReconciliationReport.build(
        expected_source_rows=1,
        entries=[entry],
    )

    assert entry.validate() == ()
    assert report.is_valid is True


def test_rejected_row_always_blocks_automatic_validation():
    entry = MigrationLedgerEntry(
        source_system="noethys",
        source_table="reglements",
        source_id="9",
        disposition=MigrationDisposition.REJECTED,
        reason_code="ORPHAN_PAYMENT",
    )
    report = ReconciliationReport.build(
        expected_source_rows=1,
        entries=[entry],
    )

    assert report.rejected_rows == 1
    assert report.is_valid is False


def test_duplicate_source_identity_blocks_validation():
    report = ReconciliationReport.build(
        expected_source_rows=2,
        entries=[_entry(7), _entry(7, destination_id="p-7-bis")],
    )

    assert report.duplicated_sources == (("noethys", "personnes", "7"),)
    assert report.is_valid is False


def test_blocking_business_metric_must_match_exactly():
    report = ReconciliationReport.build(
        expected_source_rows=1,
        entries=[_entry(1)],
        metrics=[
            ReconciliationMetric(
                code="TOTAL_REMBOURSEMENTS_CENTS",
                source_value=18745237,
                destination_value=18745236,
                blocking=True,
            )
        ],
    )

    assert len(report.blocking_metric_mismatches) == 1
    assert report.is_valid is False


def test_non_blocking_informational_metric_does_not_block():
    report = ReconciliationReport.build(
        expected_source_rows=1,
        entries=[_entry(1)],
        metrics=[
            ReconciliationMetric(
                code="LEGACY_CACHE_SIZE",
                source_value=100,
                destination_value=0,
                blocking=False,
            )
        ],
    )

    assert report.is_valid is True