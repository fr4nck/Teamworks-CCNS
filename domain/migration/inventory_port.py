"""Port d'inventaire moteur-indépendant.

Un adaptateur (SQLite, MySQL, ...) implémente ce protocole. Le moteur
d'inventaire (inventory_engine.py) ne connaît que cette interface : il ne
sait pas s'il parle à SQLite, MySQL, ou à un double de test.
"""

from __future__ import annotations

from typing import Iterator, Protocol

from domain.migration.inventory_model import ColumnDefinition, ColumnStats


class LegacyDatabasePort(Protocol):
    engine_name: str
    engine_version: str
    source_label: str

    def list_tables(self) -> tuple[str, ...]:
        """Liste des tables réelles (hors tables système du moteur)."""
        ...

    def row_count(self, table: str) -> int:
        ...

    def column_definitions(self, table: str) -> tuple[ColumnDefinition, ...]:
        ...

    def column_stats(
        self, table: str, column: ColumnDefinition, *, sample_limit: int
    ) -> ColumnStats:
        """Statistiques d'une colonne, calculées par agrégation SQL côté moteur."""
        ...

    def duplicate_key_row_count(self, table: str, key_columns: tuple[str, ...]) -> int:
        """Nombre de lignes excédentaires pour des valeurs de clé dupliquées."""
        ...

    def rows_without_usable_key(self, table: str, key_columns: tuple[str, ...]) -> int:
        """Nombre de lignes dont au moins une colonne de clé est NULL."""
        ...

    def fetch_rows(
        self, table: str, columns: tuple[str, ...]
    ) -> Iterator[tuple[object, ...]]:
        """Itère les lignes d'une table pour un sous-ensemble de colonnes.

        Réservé aux tables de taille maîtrisée (ex. le pilote Frais) : ne
        doit jamais être utilisé pour une agrégation qu'une requête SQL
        pourrait calculer directement.
        """
        ...
