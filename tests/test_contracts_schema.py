import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "teamworks" / "Utils" / "UTILS_Contrats_schema.py"
spec = importlib.util.spec_from_file_location("UTILS_Contrats_schema", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeDB:
    def __init__(self, fields_by_table):
        if isinstance(fields_by_table, dict):
            self.fields_by_table = {name: list(fields) for name, fields in fields_by_table.items()}
        else:
            self.fields_by_table = {"contrats": list(fields_by_table)}
        self.add_calls = []

    def GetListeChamps2(self, nomTable):
        return list(self.fields_by_table.get(nomTable, []))

    def AjoutChamp(self, nomTable="", nomChamp="", typeChamp=""):
        self.add_calls.append((nomTable, nomChamp, typeChamp))
        self.fields_by_table.setdefault(nomTable, []).append((nomChamp, typeChamp))


EXPECTED_CONTRACT_COLUMNS = (
    "cee_qualification",
    "convention_code",
    "ccns_group",
    "weekly_hours",
    "gross_monthly_salary",
    "gross_annual_salary",
    "operation_type",
    "previous_contract_id",
    "trial_period_value",
    "trial_period_unit",
)


class ContractSchemaTests(unittest.TestCase):
    def test_adds_cee_qualification_once_on_legacy_database(self):
        db = FakeDB([
            ("IDcontrat", "INTEGER"),
            ("IDclassification", "INTEGER"),
            ("IDtype", "INTEGER"),
        ])

        self.assertTrue(module.EnsureCEEQualificationColumn(db))
        self.assertEqual(
            db.add_calls,
            [("contrats", "cee_qualification", "VARCHAR(32)")],
        )
        self.assertFalse(module.EnsureCEEQualificationColumn(db))
        self.assertEqual(len(db.add_calls), 1)

    def test_adds_all_contract_engine_columns_idempotently(self):
        db = FakeDB([
            ("IDcontrat", "INTEGER"),
            ("IDclassification", "INTEGER"),
            ("IDtype", "INTEGER"),
        ])

        created = module.EnsureContractEngineColumns(db)

        self.assertEqual(created, EXPECTED_CONTRACT_COLUMNS)
        self.assertEqual(
            db.add_calls,
            [
                ("contrats", "cee_qualification", "VARCHAR(32)"),
                ("contrats", "convention_code", "VARCHAR(32)"),
                ("contrats", "ccns_group", "VARCHAR(8)"),
                ("contrats", "weekly_hours", "REAL"),
                ("contrats", "gross_monthly_salary", "REAL"),
                ("contrats", "gross_annual_salary", "REAL"),
                ("contrats", "operation_type", "VARCHAR(24)"),
                ("contrats", "previous_contract_id", "INTEGER"),
                ("contrats", "trial_period_value", "INTEGER"),
                ("contrats", "trial_period_unit", "VARCHAR(8)"),
            ],
        )

        self.assertEqual(module.EnsureContractEngineColumns(db), ())
        self.assertEqual(len(db.add_calls), len(EXPECTED_CONTRACT_COLUMNS))

    def test_preserves_existing_partial_schema(self):
        db = FakeDB([
            ("IDcontrat", "INTEGER"),
            ("cee_qualification", "VARCHAR(32)"),
            ("convention_code", "VARCHAR(32)"),
        ])

        created = module.EnsureContractEngineColumns(db)
        self.assertEqual(created, EXPECTED_CONTRACT_COLUMNS[2:])

    def test_adds_contract_model_discriminants_idempotently(self):
        db = FakeDB({
            "contrats_modeles": [
                ("IDmodele", "INTEGER"),
                ("IDclassification", "INTEGER"),
                ("IDtype", "INTEGER"),
            ]
        })

        created = module.EnsureContractModelColumns(db)

        self.assertEqual(created, ("cee_qualification", "convention_code", "ccns_group"))
        self.assertEqual(
            db.add_calls,
            [
                ("contrats_modeles", "cee_qualification", "VARCHAR(32)"),
                ("contrats_modeles", "convention_code", "VARCHAR(32)"),
                ("contrats_modeles", "ccns_group", "VARCHAR(8)"),
            ],
        )
        self.assertEqual(module.EnsureContractModelColumns(db), ())

    def test_does_nothing_when_cee_column_already_exists(self):
        db = FakeDB([
            ("IDcontrat", "INTEGER"),
            ("cee_qualification", "VARCHAR(32)"),
        ])

        self.assertFalse(module.EnsureCEEQualificationColumn(db))
        self.assertEqual(db.add_calls, [])

    def test_rejects_missing_database(self):
        with self.assertRaises(ValueError):
            module.EnsureCEEQualificationColumn(None)
        with self.assertRaises(ValueError):
            module.EnsureContractModelColumns(None)


if __name__ == "__main__":
    unittest.main()
