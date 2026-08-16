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
        self.assertIn("wx.CallAfter(self.EndModal, wx.ID_CANCEL)", source)

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

    def test_selection_periode_no_align_right_in_horizontal_sizer(self):
        source = self.read_source("teamworks/Dlg/DLG_Selection_periode.py")

        self.assertNotIn("wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL", source)

    def test_page_generalites_importation_guard_missing_person(self):
        source = self.read_source("teamworks/Ctrl/CTRL_Page_generalites.py")

        self.assertNotIn("donnees = DB.ResultatReq()[0]\n        DB.Close()", source)
        self.assertIn("Cette personne n'existe plus dans la base de données.", source)

    def test_page_generalites_set_pays_guard(self):
        source = self.read_source("teamworks/Ctrl/CTRL_Page_generalites.py")

        self.assertIn("if not pays:\n            return", source)

    def test_ctrl_personnes_on_select_guard(self):
        source = self.read_source("teamworks/Ctrl/CTRL_Personnes.py")

        self.assertNotIn("donnees = DB.ResultatReq()[0]", source)
        self.assertIn("if not resultats:", source)

    def test_ctrl_recrutement_maj_identite_guard(self):
        source = self.read_source("teamworks/Ctrl/CTRL_Recrutement.py")

        self.assertNotIn("donnees = DB.ResultatReq()[0]", source)
        self.assertIn("if not resultats:", source)

    def test_saisie_candidat_importation_guard(self):
        source = self.read_source("teamworks/Dlg/DLG_Saisie_candidat.py")

        self.assertNotIn("listeDonnees = DB.ResultatReq()[0]", source)
        self.assertIn("if not resultats:", source)
        self.assertIn("Ce candidat n'existe plus dans la base de données.", source)

    def test_saisie_coords_importation_guard(self):
        source = self.read_source("teamworks/Dlg/DLG_Saisie_coords.py")

        self.assertNotIn("donnees = DB.ResultatReq()[0]", source)
        self.assertIn("if not resultats:", source)
        self.assertIn("Cette coordonnée n'existe plus dans la base de données.", source)
        self.assertIn("wx.CallAfter(self.EndModal, wx.ID_CANCEL)", source)

    def test_edition_due_guard_missing_contrat(self):
        source = self.read_source("teamworks/Dlg/DLG_Edition_DUE.py")

        self.assertNotIn("listeContrat = DB.ResultatReq()[0]", source)
        self.assertNotIn("listePersonne = DB.ResultatReq()[0]", source)
        self.assertIn("if not resultats:", source)

    def test_edition_due_guard_secondary_lookups(self):
        source = self.read_source("teamworks/Dlg/DLG_Edition_DUE.py")

        self.assertNotIn("listeClassification = DB.ResultatReq()[0]", source)
        self.assertNotIn("listeType = DB.ResultatReq()[0]", source)
        self.assertNotIn("listeValeursPoint = DB.ResultatReq()[0]", source)
        self.assertNotIn("nationalite = listePays[0][0]\n", source)
        self.assertNotIn("pays_naiss = listePays[0][0]\n", source)
        self.assertIn("if listePays else", source)

    def test_ol_candidats_convert_guard_missing_candidat(self):
        source = self.read_source("teamworks/Ol/OL_candidats.py")

        self.assertNotIn("listeDonnees = DB.ResultatReq()[0]", source)
        self.assertIn("if not resultats:", source)

    def test_publipostage_donnees_guard_secondary_lookups(self):
        source = self.read_source("teamworks/Utils/UTILS_Publipostage_donnees.py")

        self.assertNotIn('DB.ResultatReq()[0][0]', source)
        self.assertIn('if resultats else ""', source)

    def test_afficher_offres_externes_default_disabled(self):
        """Le paramètre afficher_offres_externes doit être absent de la base => défaut False."""
        source_aide = self.read_source("teamworks/Utils/UTILS_Aide.py")
        source_tw = self.read_source("teamworks/Teamworks.py")

        # La porte DLG_Financement est conditionnelle dans UTILS_Aide.Aide()
        self.assertIn('GetParametre("afficher_offres_externes", defaut=False)', source_aide)
        self.assertNotIn(
            "dlg = DLG_Financement.Dialog(None, code=\"documentation\")\n        dlg.ShowModal() \n        dlg.Destroy()\n        return",
            source_aide,
        )

        # AnnonceFinancement court-circuite si offres désactivées
        self.assertIn('GetParametre("afficher_offres_externes", defaut=False)', source_tw)
        self.assertIn("def AnnonceFinancement(self):", source_tw)
        idx_annonce = source_tw.index("def AnnonceFinancement(self):")
        bloc_annonce = source_tw[idx_annonce: idx_annonce + 200]
        self.assertIn("return False", bloc_annonce)

        # On_propos_soutenir est protégé
        self.assertIn("def On_propos_soutenir(self, event):", source_tw)
        idx_soutenir = source_tw.index("def On_propos_soutenir(self, event):")
        bloc_soutenir = source_tw[idx_soutenir: idx_soutenir + 200]
        self.assertIn("return", bloc_soutenir)

        # Handler de paramétrage présent
        self.assertIn("def On_param_offres_externes(self, event):", source_tw)
        self.assertIn("SetParametre(\"afficher_offres_externes\",", source_tw)

        # Item de menu déclaré
        self.assertIn('"offres_externes"', source_tw)


if __name__ == "__main__":
    unittest.main()
