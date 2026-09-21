from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_email_extensions_sont_embarquees_explicitement():
    ci = _read(".github/workflows/ci.yml")
    for module in ("wx.richtext", "wx._richtext", "wx._xml"):
        assert "'--hidden-import', '%s'" % module in ci
    assert "Extension wx._xml absente du paquet Windows" in ci
    assert "import wx._xml" in ci


def test_vacances_actions_ne_s_etirent_plus():
    source = _read("teamworks/Dlg/DLG_Vacances.py")
    assert "sizer_actions = wx.BoxSizer(wx.HORIZONTAL)" in source
    assert "sizer_actions.AddStretchSpacer(1)" in source
    assert "sizer_actions = wx.WrapSizer" not in source
    assert "Importer depuis l’Éducation nationale" in source


def test_boutons_actions_communs_gardent_leur_largeur_naturelle():
    source = _read("teamworks/Ctrl/CTRL_Bouton_image.py")
    assert "SetMaxSize((largeur_min, -1))" in source
    assert "transforme pas le bouton en barre" in source


def test_bandeau_problemes_est_plat_et_arrete_avant_fermeture():
    source = _read("teamworks/Dlg/DLG_Fiche_individuelle_core.py")
    assert "self.bitmap_problemes_G = None" in source
    assert "self.bitmap_problemes_D = None" in source
    layout = source.split("sizer_problemes = wx.BoxSizer", 1)[1].split(
        "sizer_header =", 1
    )[0]
    assert "bitmap_problemes_G" not in layout
    assert "bitmap_problemes_D" not in layout
    fermer = source.split("def Fermer(self, save=True):", 1)[1].split(
        "def Verifie_validite_donnees", 1
    )[0]
    assert "self._fermeture_en_cours" in fermer
    assert "self.txtDefilant.Stop()" in fermer


def test_rafraichissement_barre_ne_rouvre_plus_mysql_a_chaque_focus():
    source = _read("teamworks/Dlg/DLG_Fiche_individuelle_core.py")
    bloc = source.split("def MAJ_txt_pb_personne(self):", 1)[1].split(
        "def MaJ_header", 1
    )[0]
    assert "Recherche_problemes_personnes(" not in bloc
    assert "Recup_liste_pb_personnes()" in bloc


def test_publipostage_personnes_reutilise_connexion_reseau():
    source = _read("teamworks/Ol/OL_personnes.py")
    bloc = source.split("def CourrierPublipostage", 1)[1].split(
        "def Supprimer", 1
    )[0]
    assert "connexions_reseau_partagees" in bloc
    assert "wx.personnes.publipostage.donnees" in bloc


def test_generalites_force_la_taille_virtuelle_apres_reparentage():
    source = _read("teamworks/Ctrl/CTRL_Page_generalites_091e.py")
    assert "def _rafraichir_taille_virtuelle" in source
    assert "section.InvalidateBestSize()" in source
    assert "self._scroll_host.SetVirtualSize" in source
    assert "self._rafraichir_taille_virtuelle()" in source


def test_aide_ouvre_la_documentation_publiee():
    source = _read("teamworks/Utils/UTILS_Aide.py")
    assert "https://fr4nck.github.io/Teamworks-CCNS/" in source
    assert "wx.LaunchDefaultBrowser" in source
    assert "en cours de centralisation" not in source
    assert '"Vacances": "administration/parametrage/"' in source


def test_ressources_historiques_sont_activees_par_defaut_et_configurables():
    customize = _read("teamworks/Utils/UTILS_Customize.py")
    prefs = _read("teamworks/Dlg/DLG_Preferences.py")
    app = _read("teamworks/Teamworks.py")
    installer = _read("packaging/windows/Teamworks-CCNS.iss")

    assert '("afficher_ressources", "1")' in customize
    assert "self.ressources_historiques = wx.CheckBox" in prefs
    assert '"1" if self.ressources_historiques.GetValue() else "0"' in prefs
    assert "Forum historique Teamworks / Noethys" in app
    assert "Tutoriels historiques Teamworks / Noethys" in app
    assert "Documentation Teamworks-CCNS" in app
    assert "LegacyResourcesPage" in installer
    assert "ExistingValue <> '0'" in installer
    assert "SetIniString(" in installer


def test_updater_historique_ne_contacte_plus_le_reseau_au_demarrage():
    app = _read("teamworks/Teamworks.py")
    gadget = _read("teamworks/Gadget.py")
    bloc = app.split("def RechercheMAJinternet(self):", 1)[1].split(
        "@staticmethod", 1
    )[0]
    assert "return False" in bloc
    assert "Mise à jour automatique n'est pas activée" in gadget
    assert "Une nouvelle version du logiciel est disponible" not in gadget
