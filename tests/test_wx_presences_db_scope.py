import importlib.util
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "teamworks/Utils/UTILS_Connexion_partagee.py"
PRESENCES = ROOT / "teamworks/Ctrl/CTRL_Presences.py"
NAVIGATION = ROOT / "teamworks/Ctrl/CTRL_Navigation_principale.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def _charger_scope():
    spec = importlib.util.spec_from_file_location("scope_connexions_test", SCOPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _CurseurFaux(object):
    def __init__(self):
        self.close_count = 0

    def close(self):
        self.close_count += 1


class _ConnexionFausse(object):
    __hash__ = None

    def __init__(self):
        self.rollback_count = 0
        self.close_count = 0
        self.curseurs = []

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.close_count += 1

    def cursor(self):
        curseur = _CurseurFaux()
        self.curseurs.append(curseur)
        return curseur


def test_scope_reutilise_une_connexion_sequentielle_et_ferme_en_sortie():
    scope = _charger_scope()
    connexions = []

    def ouvrir(nom_fichier):
        connexion = _ConnexionFausse()
        connexions.append(connexion)
        return connexion, "base_tdata"

    gestion_db = SimpleNamespace(GetConnexionReseau=ouvrir)

    with scope.connexions_reseau_partagees(gestion_db) as stats:
        bail1, nom1 = gestion_db.GetConnexionReseau("3306;h;u;p[RESEAU]base_TDATA")
        assert nom1 == "base_tdata"
        curseur1 = bail1.cursor()
        bail1.close()

        bail2, nom2 = gestion_db.GetConnexionReseau("3306;h;u;p[RESEAU]base_TDATA")
        assert nom2 == "base_tdata"
        curseur2 = bail2.cursor()
        bail2.close()

        assert len(connexions) == 1
        assert stats["ouvertures_physiques"] == 1
        assert stats["reutilisations"] == 1
        assert connexions[0].rollback_count == 2
        assert connexions[0].close_count == 0
        assert curseur1.close_count == 1
        assert curseur2.close_count == 1

    assert connexions[0].close_count == 1


def test_scope_ne_partage_pas_deux_db_ouvertes_en_meme_temps():
    scope = _charger_scope()
    connexions = []

    def ouvrir(nom_fichier):
        connexion = _ConnexionFausse()
        connexions.append(connexion)
        return connexion, "base_tdata"

    gestion_db = SimpleNamespace(GetConnexionReseau=ouvrir)

    with scope.connexions_reseau_partagees(gestion_db) as stats:
        bail1, _ = gestion_db.GetConnexionReseau("x[RESEAU]base_TDATA")
        bail2, _ = gestion_db.GetConnexionReseau("x[RESEAU]base_TDATA")
        assert len(connexions) == 2
        assert stats["ouvertures_physiques"] == 2
        bail2.close()
        bail1.close()

    assert sum(connexion.close_count for connexion in connexions) == 2


def test_scope_ferme_physiquement_meme_si_action_leve_une_exception():
    scope = _charger_scope()
    connexion = _ConnexionFausse()
    gestion_db = SimpleNamespace(
        GetConnexionReseau=lambda nom_fichier: (connexion, "base_tdata")
    )

    try:
        with scope.connexions_reseau_partagees(gestion_db):
            gestion_db.GetConnexionReseau("x[RESEAU]base_TDATA")
            raise RuntimeError("test")
    except RuntimeError:
        pass

    assert connexion.close_count == 1


def test_presences_supprime_les_deux_redondances_mesurees():
    source = _source(PRESENCES)
    assert "self.panelCalendrier.SetSelectionDates(selectionDates)" in source
    assert "self.panelCalendrier.MAJselectionDates" not in source
    assert "presents_connus = self.panelPlanning.RecherchePresents" in source
    assert "lambda _dates: list(presents_connus)" in source
    assert "ConnexionPartagee.connexions_reseau_partagees(GestionDB)" in source


def test_navigation_mesure_le_vrai_panel_individus():
    source = _source(NAVIGATION)
    assert '"wx.personnes.panel.majpanel"' in source
    assert 'page.GetName() == "Personnes"' in source
    assert 'getattr(page, "init", False)' in source


def test_nouveaux_fichiers_compilent():
    for path in (SCOPE, PRESENCES, NAVIGATION):
        compile(_source(path), str(path), "exec")
