import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "teamworks" / "Utils" / "UTILS_Contrats_modeles_documents.py"
spec = importlib.util.spec_from_file_location("UTILS_Contrats_modeles_documents", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CompatibilityTests(unittest.TestCase):
    def test_legacy_file_remains_available(self):
        self.assertTrue(module.IsCompatible({"CONVENTION_CODE": "CCNS", "GROUPECCNS": "G1"}, None))

    def test_ccns_exact_and_generic(self):
        contract = {"CONVENTION_CODE": "CCNS", "GROUPECCNS": "G1"}
        self.assertTrue(module.IsCompatible(contract, {"convention_code": "CCNS", "ccns_group": "G1", "cee_qualification": None}))
        self.assertTrue(module.IsCompatible(contract, {"convention_code": "CCNS", "ccns_group": None, "cee_qualification": None}))
        self.assertFalse(module.IsCompatible(contract, {"convention_code": "CCNS", "ccns_group": "G4", "cee_qualification": None}))
        self.assertFalse(module.IsCompatible(contract, {"convention_code": "CEE", "ccns_group": None, "cee_qualification": None}))

    def test_cee_exact_and_generic(self):
        contract = {"CONVENTION_CODE": "CEE", "QUALIFICATIONCEE_CODE": "BAFA_HOLDER"}
        self.assertTrue(module.IsCompatible(contract, {"convention_code": "CEE", "ccns_group": None, "cee_qualification": "BAFA_HOLDER"}))
        self.assertTrue(module.IsCompatible(contract, {"convention_code": "CEE", "ccns_group": None, "cee_qualification": None}))
        self.assertFalse(module.IsCompatible(contract, {"convention_code": "CEE", "ccns_group": None, "cee_qualification": "BAFA_TRAINEE"}))
        self.assertFalse(module.IsCompatible(contract, {"convention_code": "CCNS", "ccns_group": "G1", "cee_qualification": None}))

    def test_explicit_global_metadata_is_compatible(self):
        self.assertTrue(module.IsCompatible({"CONVENTION_CODE": "CCNS"}, {"convention_code": None, "ccns_group": None, "cee_qualification": None}))


if __name__ == "__main__":
    unittest.main()
