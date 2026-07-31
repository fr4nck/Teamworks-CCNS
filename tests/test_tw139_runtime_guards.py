from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RuntimeGuardRegressionTests(unittest.TestCase):
    def read_source(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_photo_actions_guard_missing_people(self):
        source = self.read_source("teamworks/Ctrl/CTRL_Photo.py")

        self.assertNotIn("civilite = DB.ResultatReq()[0][0]", source)
        self.assertNotIn("donnees = DB.ResultatReq()[0]", source)
        self.assertGreaterEqual(source.count("if not resultats:"), 2)
        self.assertIn("Cette personne n'existe plus dans la base de données.", source)

    def test_contract_fields_accept_null_database_values(self):
        source = self.read_source("teamworks/Dlg/DLG_Saisie_champs_contrats.py")

        for index in (1, 2, 3, 4, 5):
            self.assertIn(f"donnees[{index}] or \"\"", source)
        self.assertIn("self.text_exemple.SetFocus()", source)


if __name__ == "__main__":
    unittest.main()
