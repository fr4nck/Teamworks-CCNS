from dataclasses import dataclass, field
from datetime import datetime

from domain.migration.inventory_engine import build_database_inventory
from domain.migration.inventory_model import ColumnDefinition, ColumnStats


@dataclass
class _FakePort:
    """Double de test du port d'inventaire, sans aucun moteur SQL réel."""

    engine_name: str = "fake"
    engine_version: str = "1.0"
    source_label: str = "fake-source"
    tables_data: dict = field(default_factory=dict)

    def list_tables(self) -> tuple[str, ...]:
        return tuple(self.tables_data)

    def row_count(self, table: str) -> int:
        return len(self.tables_data[table]["rows"])

    def column_definitions(self, table: str) -> tuple[ColumnDefinition, ...]:
        return self.tables_data[table]["columns"]

    def column_stats(self, table: str, column: ColumnDefinition, *, sample_limit: int) -> ColumnStats:
        values = [row[column.name] for row in self.tables_data[table]["rows"]]
        non_null = [v for v in values if v is not None]
        return ColumnStats(
            column=column,
            row_count=len(values),
            null_count=sum(1 for v in values if v is None),
            empty_string_count=sum(1 for v in values if v == ""),
            zero_count=sum(1 for v in values if v == 0),
            distinct_count=len(set(non_null)),
            sample_values=tuple(str(v) for v in non_null[:sample_limit]),
        )

    def duplicate_key_row_count(self, table: str, key_columns: tuple[str, ...]) -> int:
        column = key_columns[0]
        keys = [row[column] for row in self.tables_data[table]["rows"]]
        seen: dict = {}
        surplus = 0
        for key in keys:
            seen[key] = seen.get(key, 0) + 1
        for count in seen.values():
            if count > 1:
                surplus += count - 1
        return surplus

    def rows_without_usable_key(self, table: str, key_columns: tuple[str, ...]) -> int:
        column = key_columns[0]
        return sum(1 for row in self.tables_data[table]["rows"] if row[column] is None)

    def fetch_rows(self, table: str, columns: tuple[str, ...]):
        for row in self.tables_data[table]["rows"]:
            yield tuple(row[c] for c in columns)


def test_empty_database_has_no_tables():
    port = _FakePort(tables_data={})

    inventory = build_database_inventory(port, inventoried_at=datetime(2026, 1, 1))

    assert inventory.table_count == 0
    assert inventory.total_row_count == 0
    assert inventory.tables == ()


def test_empty_table_reports_zero_rows():
    id_col = ColumnDefinition(name="id", declared_type="INTEGER", nullable=False, is_primary_key=True)
    port = _FakePort(tables_data={"vide": {"columns": (id_col,), "rows": []}})

    inventory = build_database_inventory(port, inventoried_at=datetime(2026, 1, 1))

    table = inventory.table("vide")
    assert table is not None
    assert table.row_count == 0
    assert table.columns[0].null_count == 0


def test_duplicate_primary_key_is_counted():
    id_col = ColumnDefinition(name="id", declared_type="INTEGER", nullable=False, is_primary_key=True)
    port = _FakePort(
        tables_data={
            "t": {
                "columns": (id_col,),
                "rows": [{"id": 1}, {"id": 1}, {"id": 2}],
            }
        }
    )

    inventory = build_database_inventory(port, inventoried_at=datetime(2026, 1, 1))

    table = inventory.table("t")
    assert table.duplicate_key_row_count == 1


def test_null_primary_key_counts_as_row_without_usable_key():
    id_col = ColumnDefinition(name="id", declared_type="INTEGER", nullable=True, is_primary_key=True)
    port = _FakePort(
        tables_data={"t": {"columns": (id_col,), "rows": [{"id": 1}, {"id": None}]}}
    )

    inventory = build_database_inventory(port, inventoried_at=datetime(2026, 1, 1))

    table = inventory.table("t")
    assert table.rows_without_usable_key == 1


def test_sensitive_column_is_masked_in_output():
    nom_col = ColumnDefinition(name="nom", declared_type="VARCHAR(100)", nullable=True)
    port = _FakePort(
        tables_data={"personnes": {"columns": (nom_col,), "rows": [{"nom": "Dupont"}]}}
    )

    inventory = build_database_inventory(port, inventoried_at=datetime(2026, 1, 1))

    table = inventory.table("personnes")
    assert table.columns[0].sample_values == ()


def test_result_is_deterministic_given_same_timestamp():
    id_col = ColumnDefinition(name="id", declared_type="INTEGER", nullable=False, is_primary_key=True)
    port = _FakePort(tables_data={"t": {"columns": (id_col,), "rows": [{"id": 1}]}})
    ts = datetime(2026, 1, 1)

    first = build_database_inventory(port, inventoried_at=ts)
    second = build_database_inventory(port, inventoried_at=ts)

    assert first == second
