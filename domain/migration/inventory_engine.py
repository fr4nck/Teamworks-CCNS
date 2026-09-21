"""Construction de l'inventaire moteur-indépendant d'une base historique.

Ce module ne fait qu'orchestrer les appels au port : il ne contient aucune
requête SQL et ne sait rien d'un moteur particulier.
"""

from __future__ import annotations

from datetime import datetime

from domain.migration.inventory_model import DatabaseInventory, TableInventory
from domain.migration.inventory_port import LegacyDatabasePort

DEFAULT_SAMPLE_LIMIT = 3


def build_database_inventory(
    port: LegacyDatabasePort,
    *,
    sample_limit: int = DEFAULT_SAMPLE_LIMIT,
    inventoried_at: datetime | None = None,
) -> DatabaseInventory:
    tables: list[TableInventory] = []
    total_rows = 0

    for table_name in port.list_tables():
        row_count = port.row_count(table_name)
        total_rows += row_count

        columns_def = port.column_definitions(table_name)
        primary_key_columns = tuple(c.name for c in columns_def if c.is_primary_key)

        column_stats = []
        for column in columns_def:
            # Une colonne sensible ne doit jamais faire l'objet d'une requête
            # d'échantillonnage : sample_limit=0 empêche le port de lire la
            # moindre valeur, pas seulement de l'afficher après coup.
            effective_sample_limit = 0 if column.is_sensitive else sample_limit
            stats = port.column_stats(
                table_name, column, sample_limit=effective_sample_limit
            )
            column_stats.append(stats.masked if column.is_sensitive else stats)

        if primary_key_columns:
            duplicate_key_row_count = port.duplicate_key_row_count(
                table_name, primary_key_columns
            )
            rows_without_usable_key = port.rows_without_usable_key(
                table_name, primary_key_columns
            )
        else:
            duplicate_key_row_count = 0
            rows_without_usable_key = row_count

        tables.append(
            TableInventory(
                name=table_name,
                row_count=row_count,
                primary_key_columns=primary_key_columns,
                columns=tuple(column_stats),
                rows_without_usable_key=rows_without_usable_key,
                duplicate_key_row_count=duplicate_key_row_count,
            )
        )

    return DatabaseInventory(
        engine=port.engine_name,
        engine_version=port.engine_version,
        source_label=port.source_label,
        inventoried_at=inventoried_at or datetime.now(),
        table_count=len(tables),
        total_row_count=total_rows,
        tables=tuple(tables),
    )
