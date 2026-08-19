from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
if str(TEAMWORKS) not in sys.path:
    sys.path.insert(0, str(TEAMWORKS))

from Data import DATA_Tables
from Utils import UTILS_Contrats_schema


def _types(table_name):
    return {name: type_name for name, type_name, *_ in DATA_Tables.DB_DATA[table_name]}


def test_canonical_contract_schema_contains_all_runtime_tw184_columns() -> None:
    contract_types = _types("contrats")
    for name, type_name in UTILS_Contrats_schema.ADDITIVE_COLUMNS:
        assert contract_types.get(name) == type_name

    model_types = _types("contrats_modeles")
    for name, type_name in UTILS_Contrats_schema.MODEL_ADDITIVE_COLUMNS:
        assert model_types.get(name) == type_name


def test_canonical_schema_preserves_cee_rates_and_document_targeting_on_repair() -> None:
    cee = _types("contrats_cee_baremes")
    assert cee == {
        "IDbareme": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "qualification": "VARCHAR(32)",
        "montant_journalier": "REAL",
        "date_debut": "DATE",
    }

    documents = _types("contrats_documents_modeles")
    assert documents == {
        "IDdocument_modele": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "nom_fichier": "VARCHAR(255)",
        "convention_code": "VARCHAR(32)",
        "ccns_group": "VARCHAR(8)",
        "cee_qualification": "VARCHAR(32)",
    }


def test_optional_contract_import_includes_tw184_configuration_tables() -> None:
    contract_group = next(
        tables
        for label, tables, enabled in DATA_Tables.TABLES_IMPORTATION_OPTIONNELLES
        if label == u"Données de contrats"
    )
    assert "contrats_cee_baremes" in contract_group
    assert "contrats_documents_modeles" in contract_group
