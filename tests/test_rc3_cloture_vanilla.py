import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_version_canonique_et_runtime_aligne():
    version = _read("VERSION").strip()
    assert re.fullmatch(r"0\.9\.2-rc[1-9]\d*", version)
    assert f"Statut actuel : `{version}`" in _read("README.md")
    assert _read("teamworks/Versions.txt").splitlines()[0] == f"Version {version} :"
    assert _read("CHANGELOG.md").startswith(f"# Teamworks-CCNS {version.split('-')[0]}")
    source = _read("teamworks/Teamworks.py")
    assert 'Chemins.GetMainPath("VERSION")' in source
    assert "VERSION_APPLICATION = _lire_version_teamworks_ccns()" in source
    assert "CORE.VERSION_APPLICATION = VERSION_APPLICATION" in source
    assert "Teamworks CCNS %s" in source
    assert "Activer_rapport_erreurs(version=VERSION_APPLICATION)" in source


def test_individus_rendu_atomique_et_pas_de_largeur_forcee_au_resize():
    source = _read("teamworks/Ctrl/CTRL_Personnes.py")
    assert "self.Freeze()" in source
    assert "self.Thaw()" in source
    assert "AjusterColonnes" not in source
    assert "SetColumnWidth" not in source
    assert "listCtrl_personnes.Bind(wx.EVT_SIZE" not in source
    assert 'view_id="personnes.main"' in source


def test_individus_connexion_bornee_pour_liste_et_arbre():
    liste = _read("teamworks/Ol/OL_personnes.py")
    arbre = _read("teamworks/Utils/UTILS_Personnes_performance.py")
    assert "self._db_action = CORE.GestionDB.DB()" in liste
    assert "self._db_action.Close()" in liste
    assert "def Importation_pays(self):" in liste
    assert "def InitModel(self):" in liste
    assert "def GetTracks(self):" in liste
    assert "def _contrats_en_cours_ou_a_venir(DB):" in arbre
    assert "Recherche_problemes_personnes(tuple(liste_ids), DB=DB)" in arbre


def test_telephones_reste_redimensionnable_et_persistant():
    core = _read("teamworks/Ol/OL_personnes_core.py")
    modern = _read("teamworks/Ol/OL_personnes.py")
    dialog = _read("teamworks/Dlg/DLG_Config_liste_personnes.py")
    assert '_(u"Téléphones"), "left", 200, "telephones"' in core
    assert "minWidth" not in core.split('_(u"Téléphones")', 1)[1].split("\n", 1)[0]
    assert "EVT_LIST_COL_END_DRAG" in modern
    assert "_sauvegarder_presentation_colonnes" in modern
    assert "wx_personnes_etat_colonnes_v1" in modern
    assert "reinitialiser_presentation" in dialog
    assert "largeurs_defaut" in dialog


def test_aide_ouvre_la_documentation_ccns_sans_parcours_commercial():
    aide = _read("teamworks/Utils/UTILS_Aide.py")
    assert "DLG_Financement" not in aide
    assert "teamworks.ovh" not in aide.lower()
    assert "https://fr4nck.github.io/Teamworks-CCNS/" in aide
    assert "wx.LaunchDefaultBrowser" in aide


def test_menu_runtime_garde_les_credits_et_filtre_les_ressources_historiques():
    source = _read("teamworks/Teamworks.py")
    assert "_LIBELLES_COMMERCIAUX_A_RETIRER" in source
    assert "_LIBELLES_RESSOURCES_HISTORIQUES" in source
    assert "Forum historique Teamworks / Noethys" in source
    assert "Tutoriels historiques Teamworks / Noethys" in source
    assert "afficher_ressources" in source
    assert "menu.Delete(item)" in source


def test_demarrage_ne_declenche_plus_de_sollicitation_financiere_automatique():
    source = _read("teamworks/Teamworks.py")
    bloc = source.split("def AnnonceFinancement(self):", 1)[1].split("def SetTitleFrame", 1)[0]
    assert "return False" in bloc
    assert "DLG_Financement" not in bloc
    assert "random" not in bloc


def test_changelog_courant_est_teamworks_ccns_et_legacy_archive():
    changelog = _read("CHANGELOG.md")
    versions = _read("teamworks/Versions.txt")
    assert changelog.startswith("# Teamworks-CCNS 0.9.2")
    assert "0.9.2-rc3" in versions
    assert (ROOT / "docs/legacy/Versions_UPSTREAM.txt").is_file()
