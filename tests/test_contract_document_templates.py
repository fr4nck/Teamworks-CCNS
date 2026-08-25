import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "teamworks" / "Utils" / "UTILS_Contrats_modeles_documents.py"
spec = importlib.util.spec_from_file_location("UTILS_Contrats_modeles_documents", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CompatibilityTests(unittest.TestCase):
    def test_legacy_file_remains_available(self):
        self.assertTrue(module.IsCompatible({"CONVENTION": "CCNS", "GROUPECCNS": "G1"}, None))

    def test_ccns_exact_and_generic(self):
        contract = {"CONVENTION": "CCNS", "GROUPECCNS": "G1"}
        self.assertTrue(module.IsCompatible(contract, {"convention_code": "CCNS", "ccns_group": "G1", "cee_qualification": None}))
        self.assertTrue(module.IsCompatible(contract, {"convention_code": "CCNS", "ccns_group": None, "cee_qualification": None}))
        self.assertFalse(module.IsCompatible(contract, {"convention_code": "CCNS", "ccns_group": "G4", "cee_qualification": None}))
        self.assertFalse(module.IsCompatible(contract, {"convention_code": "CEE", "ccns_group": None, "cee_qualification": None}))

    def test_cee_exact_and_generic_from_readable_publipostage_value(self):
        contract = {"QUALIFICATIONCEE": "BAFA titulaire"}
        self.assertTrue(module.IsCompatible(contract, {"convention_code": "CEE", "ccns_group": None, "cee_qualification": "BAFA_HOLDER"}))
        self.assertTrue(module.IsCompatible(contract, {"convention_code": "CEE", "ccns_group": None, "cee_qualification": None}))
        self.assertFalse(module.IsCompatible(contract, {"convention_code": "CEE", "ccns_group": None, "cee_qualification": "BAFA_TRAINEE"}))
        self.assertFalse(module.IsCompatible(contract, {"convention_code": "CCNS", "ccns_group": "G1", "cee_qualification": None}))

    def test_explicit_global_metadata_is_compatible(self):
        self.assertTrue(module.IsCompatible({"CONVENTION": "CCNS"}, {"convention_code": None, "ccns_group": None, "cee_qualification": None}))

    def test_employee_contract_print_uses_filtered_adapter(self):
        source = (ROOT / "teamworks" / "Ctrl" / "CTRL_Page_contrats.py").read_text(encoding="utf-8")
        self.assertIn("from Dlg import DLG_Publiposteur_contrat", source)
        self.assertIn("DLG_Publiposteur_contrat.Dialog", source)

    def test_adapter_restores_vanilla_controls_after_dialog_construction(self):
        source = (ROOT / "teamworks" / "Dlg" / "DLG_Publiposteur_contrat.py").read_text(encoding="utf-8")
        self.assertIn("UTILS_Contrats_modeles_documents.FilterFilenames", source)
        self.assertIn("_base.ListCtrl_fichiers = original_list", source)
        self.assertIn("_base.Grid_donnees = original_grid", source)
        self.assertIn("Ciblage du modèle de contrat", source)
        self.assertIn("DeleteMetadata", source)

    def test_contract_grid_expands_keyword_labels_without_touching_vanilla(self):
        source = (ROOT / "teamworks" / "Dlg" / "DLG_Publiposteur_contrat.py").read_text(encoding="utf-8")
        self.assertIn("class Grid_donnees(_base.Grid_donnees):", source)
        self.assertIn("self.GetTextExtent(label)[0]", source)
        self.assertIn("self.SetRowLabelSize(max(140, min(320, largeur)))", source)
        self.assertIn("original_grid = _base.Grid_donnees", source)

    def test_modern_cee_supplies_legacy_brutjour_from_employer_rate(self):
        source = (ROOT / "teamworks" / "Dlg" / "DLG_Publiposteur_contrat.py").read_text(encoding="utf-8")
        self.assertIn("def _apply_legacy_cee_aliases(dict_donnees):", source)
        self.assertIn('document["BRUTJOUR"] = document["BAREMECEE"]', source)
        self.assertIn('motcles.append(("BRUTJOUR", "base"))', source)
        self.assertIn("_apply_legacy_cee_aliases(dict_donnees)", source)

    def test_deleted_file_drops_its_targeting_only_after_actual_removal(self):
        source = (ROOT / "teamworks" / "Dlg" / "DLG_Publiposteur_contrat.py").read_text(encoding="utf-8")
        self.assertIn("if not os.path.isfile(chemin):", source)
        self.assertIn("UTILS_Contrats_modeles_documents.DeleteMetadata(DB, nom_fichier)", source)


if __name__ == "__main__":
    unittest.main()
