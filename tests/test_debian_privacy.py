"""Tests autonomes du garde-fou du paquet Debian (sans wx, SQL ni réseau)."""

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "packaging" / "debian" / "check_privacy.py"
spec = importlib.util.spec_from_file_location("teamworks_deb_privacy", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class TestDebianPrivacy(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel in audit.REQUIRED:
            chemin = self.root / rel
            chemin.parent.mkdir(parents=True, exist_ok=True)
            chemin.write_text("Code ou métadonnées de test", encoding="utf-8")

    def ajouter(self, rel, texte="contenu fictif"):
        chemin = self.root / rel
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte, encoding="utf-8")

    def test_manifest_synthetique_autorise(self):
        self.ajouter("opt/teamworks-ccns/app/teamworks/Static/Images/Logo.svg")
        self.assertEqual(audit.examiner(self.root), 0)

    def test_dossier_de_developpement_refuse(self):
        self.ajouter("opt/teamworks-ccns/app/tests/test_exemple.py")
        self.assertEqual(audit.examiner(self.root), 1)

    def test_secret_env_refuse(self):
        self.ajouter("opt/teamworks-ccns/app/teamworks/.env", "FACTICE=1")
        self.assertEqual(audit.examiner(self.root), 1)

    def test_sauvegarde_sql_refusee(self):
        self.ajouter("opt/teamworks-ccns/app/teamworks/Static/sauvegarde.sqlite")
        self.assertEqual(audit.examiner(self.root), 1)

    def test_secret_litteral_refuse_sans_afficher_valeur(self):
        self.ajouter(
            "opt/teamworks-ccns/app/teamworks/demo.py",
            "api_key = 'CECI_EST_UN_SECRET_FICTIF'\n",
        )
        self.assertEqual(audit.examiner(self.root), 1)

    def test_dossier_home_refuse(self):
        self.ajouter("home/franck/.config/teamworks/conf.txt")
        self.assertEqual(audit.examiner(self.root), 1)


if __name__ == "__main__":
    unittest.main()
