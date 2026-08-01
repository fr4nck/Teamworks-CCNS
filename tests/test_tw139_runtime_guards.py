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

    def test_calendar_parameters_guard_missing_rows(self):
        source = self.read_source("teamworks/Dlg/DLG_Parametres_calendrier.py")

        self.assertNotIn("donnees = DB.ResultatReq()[0]", source)
        self.assertGreaterEqual(source.count("if not resultats:"), 2)
        self.assertIn("Les paramètres du calendrier sont introuvables.", source)
        self.assertIn("Les paramètres par défaut du calendrier sont introuvables.", source)
        self.assertNotIn("return\n            dlg.Destroy()", source)

    def test_saisie_piece_guard_missing_piece(self):
        source = self.read_source("teamworks/Dlg/DLG_Saisie_piece.py")

        self.assertNotIn("donnees = DB.ResultatReq()[0]", source)
        self.assertIn("if not resultats:", source)
        self.assertIn("Cette pièce n'existe plus dans la base de données.", source)
        self.assertIn("self.EndModal(wx.ID_CANCEL)", source)

    def test_saisie_presence_guard_missing_presence(self):
        source = self.read_source("teamworks/Dlg/DLG_Saisie_presence.py")

        self.assertNotIn("donnees = DB.ResultatReq()[0]", source)
        self.assertIn("if not resultats:", source)
        self.assertIn("Cette présence n'existe plus dans la base de données.", source)
        self.assertIn("return None", source)
        self.assertIn("wx.CallAfter(self.parent.EndModal, wx.ID_CANCEL)", source)

    def test_importation_vacances_guard_missing_organisateur(self):
        source = self.read_source("teamworks/Dlg/DLG_Importation_vacances.py")

        self.assertNotIn("cp, ville = DB.ResultatReq()[0]", source)
        self.assertIn("if not resultats:", source)
        self.assertIn("Les coordonnées de l'organisateur sont introuvables", source)


if __name__ == "__main__":
    unittest.main()
