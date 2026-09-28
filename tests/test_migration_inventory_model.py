from domain.migration.inventory_model import (
    ColumnDefinition,
    ColumnKind,
    ColumnStats,
    classify_declared_type,
    is_sensitive_column,
)


def test_classify_declared_type_follows_sqlite_affinity_style():
    assert classify_declared_type("INTEGER") is ColumnKind.INTEGER
    assert classify_declared_type("INT(11)") is ColumnKind.INTEGER
    assert classify_declared_type("VARCHAR(100)") is ColumnKind.TEXT
    assert classify_declared_type("TEXT") is ColumnKind.TEXT
    assert classify_declared_type("REAL") is ColumnKind.REAL
    assert classify_declared_type("FLOAT") is ColumnKind.REAL
    assert classify_declared_type("DECIMAL(10,2)") is ColumnKind.REAL
    assert classify_declared_type("DATE") is ColumnKind.DATE
    assert classify_declared_type("DATETIME") is ColumnKind.DATETIME
    assert classify_declared_type("TIMESTAMP") is ColumnKind.DATETIME
    assert classify_declared_type("BLOB") is ColumnKind.BLOB
    assert classify_declared_type("") is ColumnKind.UNKNOWN
    assert classify_declared_type(None) is ColumnKind.UNKNOWN


def test_sensitive_columns_are_detected_by_exact_name():
    assert is_sensitive_column("nom") is True
    assert is_sensitive_column("PRENOM") is True
    assert is_sensitive_column("num_secu") is True
    assert is_sensitive_column("IDpersonne") is False
    assert is_sensitive_column("distance") is False


def test_sensitive_columns_fallback_catches_unknown_variants():
    assert is_sensitive_column("adresse_facturation") is True
    assert is_sensitive_column("smtp_password_encoded") is True


def test_masked_column_stats_clears_samples_but_keeps_counts():
    column = ColumnDefinition(name="nom", declared_type="VARCHAR(100)", nullable=True)
    stats = ColumnStats(
        column=column,
        row_count=10,
        null_count=1,
        distinct_count=9,
        sample_values=("Dupont", "Martin"),
    )

    masked = stats.masked

    assert masked.sample_values == ()
    assert masked.row_count == 10
    assert masked.null_count == 1
    assert masked.distinct_count == 9


def test_masked_is_noop_when_no_samples():
    column = ColumnDefinition(name="distance", declared_type="REAL", nullable=True)
    stats = ColumnStats(column=column, row_count=5)

    assert stats.masked is stats
