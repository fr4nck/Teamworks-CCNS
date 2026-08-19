import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "teamworks" / "Utils" / "UTILS_Contrats_schema.py"
spec = importlib.util.spec_from_file_location("UTILS_Contrats_schema", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeDB:
    def __init__(self, fields):
        self.fields = list(fields)
        self.add_calls = []

    def GetListeChamps2(self, nomTable):
        assert nomTable == "contrats"
        return list(self.fields)

    def AjoutChamp(self, nomTable="", nomChamp="", typeChamp=""):
        self.add_calls.append((nomTable, nomChamp, typeChamp))
        self.fields.append((nomChamp, typeChamp))


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

    def test_does_nothing_when_column_already_exists(self):
        db = FakeDB([
            ("IDcontrat", "INTEGER"),
            ("cee_qualification", "VARCHAR(32)"),
        ])

        self.assertFalse(module.EnsureCEEQualificationColumn(db))
        self.assertEqual(db.add_calls, [])

    def test_rejects_missing_database(self):
        with self.assertRaises(ValueError):
            module.EnsureCEEQualificationColumn(None)


if __name__ == "__main__":
    unittest.main()
