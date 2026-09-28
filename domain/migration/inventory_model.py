"""Structures d'inventaire moteur-indépendant d'une base historique.

Ce module ne dépend d'aucun moteur SQL, ni de wx, ni de Qt, ni de GestionDB.
Il décrit ce qu'un inventaire doit contenir ; la mesure elle-même est
déléguée à un port (voir inventory_port.py) implémenté par un adaptateur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ColumnKind(str, Enum):
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    REAL = "REAL"
    DATE = "DATE"
    DATETIME = "DATETIME"
    BLOB = "BLOB"
    UNKNOWN = "UNKNOWN"


def classify_declared_type(declared_type: str | None) -> ColumnKind:
    """Classe un type déclaré (SQLite ou MySQL) selon une règle d'affinité.

    Suit le même principe que les règles d'affinité de type SQLite :
    la classification se fait par sous-chaîne, pas par correspondance
    exacte, pour rester tolérante aux variantes (VARCHAR(50), INT(11), ...).
    """
    text = (declared_type or "").strip().upper()
    if not text:
        return ColumnKind.UNKNOWN
    if "BLOB" in text or "BINARY" in text:
        return ColumnKind.BLOB
    if "DATETIME" in text or "TIMESTAMP" in text:
        return ColumnKind.DATETIME
    if "DATE" in text:
        return ColumnKind.DATE
    if "INT" in text:
        return ColumnKind.INTEGER
    if any(marker in text for marker in ("REAL", "FLOA", "DOUB", "DEC", "NUMERIC")):
        return ColumnKind.REAL
    if any(marker in text for marker in ("CHAR", "CLOB", "TEXT")):
        return ColumnKind.TEXT
    return ColumnKind.UNKNOWN


# Colonnes explicitement sensibles connues du schéma historique Noethys/Teamworks.
# Toute colonne de ce nom (insensible à la casse) n'est jamais échantillonnée.
DEFAULT_SENSITIVE_COLUMN_NAMES: frozenset[str] = frozenset(
    {
        "nom",
        "nom_jfille",
        "prenom",
        "civilite",
        "date_naiss",
        "cp_naiss",
        "ville_naiss",
        "num_secu",
        "adresse_resid",
        "adresse",
        "adresse1",
        "adresse2",
        "memo",
        "cadre_photo",
        "texte_photo",
        "photo",
        "signature",
        "email",
        "mail",
        "telephone",
        "tel",
        "tel_mobile",
        "portable",
        "password",
        "mot_de_passe",
        "mdp",
        "secret",
        "smtp_password",
        "smtp_mdp",
        "iban",
        "bic",
        "rib",
    }
)

# Filet de sécurité par sous-chaîne : mieux vaut masquer une colonne qui ne
# le nécessitait pas que révéler une donnée personnelle par un nom imprévu.
_SENSITIVE_SUBSTRINGS: tuple[str, ...] = (
    "password",
    "mdp",
    "secret",
    "iban",
    "email",
    "mail",
    "adresse",
    "telephone",
    "photo",
    "signature",
    "nom",
    "prenom",
    "naiss",
    "secu",
)


def is_sensitive_column(name: str) -> bool:
    lowered = name.strip().lower()
    if not lowered:
        return False
    if lowered in DEFAULT_SENSITIVE_COLUMN_NAMES:
        return True
    return any(marker in lowered for marker in _SENSITIVE_SUBSTRINGS)


@dataclass(frozen=True, slots=True)
class ColumnDefinition:
    name: str
    declared_type: str
    nullable: bool
    is_primary_key: bool = False

    @property
    def kind(self) -> ColumnKind:
        return classify_declared_type(self.declared_type)

    @property
    def is_sensitive(self) -> bool:
        return is_sensitive_column(self.name)


@dataclass(frozen=True, slots=True)
class ColumnStats:
    column: ColumnDefinition
    row_count: int
    null_count: int = 0
    empty_string_count: int = 0
    zero_count: int = 0
    distinct_count: int | None = None
    min_text_length: int | None = None
    max_text_length: int | None = None
    min_numeric: str | None = None
    max_numeric: str | None = None
    min_date: str | None = None
    max_date: str | None = None
    sample_values: tuple[str, ...] = field(default_factory=tuple)

    @property
    def masked(self) -> "ColumnStats":
        """Retourne une copie sans exemple de valeur, pour les colonnes sensibles."""
        if not self.sample_values:
            return self
        return ColumnStats(
            column=self.column,
            row_count=self.row_count,
            null_count=self.null_count,
            empty_string_count=self.empty_string_count,
            zero_count=self.zero_count,
            distinct_count=self.distinct_count,
            min_text_length=self.min_text_length,
            max_text_length=self.max_text_length,
            min_numeric=self.min_numeric,
            max_numeric=self.max_numeric,
            min_date=self.min_date,
            max_date=self.max_date,
            sample_values=(),
        )


@dataclass(frozen=True, slots=True)
class TableInventory:
    name: str
    row_count: int
    primary_key_columns: tuple[str, ...]
    columns: tuple[ColumnStats, ...]
    rows_without_usable_key: int = 0
    duplicate_key_row_count: int = 0


@dataclass(frozen=True, slots=True)
class DatabaseInventory:
    engine: str
    engine_version: str
    source_label: str
    inventoried_at: datetime
    table_count: int
    total_row_count: int
    tables: tuple[TableInventory, ...]
    source_fingerprint: str | None = None

    def table(self, name: str) -> TableInventory | None:
        for item in self.tables:
            if item.name == name:
                return item
        return None
