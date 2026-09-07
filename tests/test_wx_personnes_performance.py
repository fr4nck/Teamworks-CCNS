import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_fichiers_performance_personnes_compilent():
    for relative_path in (
        "teamworks/Utils/UTILS_Diagnostic_performance.py",
        "teamworks/Utils/UTILS_Personnes_performance.py",
        "teamworks/Ol/OL_personnes.py",
        "teamworks/Ctrl/CTRL_Gadget_pb_personnes.py",
        "teamworks/Dlg/DLG_Fiche_individuelle.py",
    ):
        compile(_source(relative_path), relative_path, "exec")


def test_scan_dossiers_ne_fait_plus_de_sql_dans_les_boucles_personnes():
    source = _source("teamworks/Utils/UTILS_Personnes_performance.py")
    tree = ast.parse(source)
    fonction = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "Recherche_problemes_personnes"
    )

    appels_sql_dans_boucle_personne = []
    for node in ast.walk(fonction):
        if not isinstance(node, (ast.For, ast.While)):
            continue
        for enfant in ast.walk(node):
            if not isinstance(enfant, ast.Call) or not isinstance(enfant.func, ast.Attribute):
                continue
            if enfant.func.attr == "ExecuterReq":
                appels_sql_dans_boucle_personne.append(enfant.lineno)

    assert appels_sql_dans_boucle_personne == []
    assert source.count("DB.ExecuterReq(") == 6
    assert "FonctionsPerso.Recherche_ContratsEnCoursOuAVenir()" in source


def test_premier_maj_de_liste_est_explicitement_ignore_une_seule_fois():
    source = _source("teamworks/Ol/OL_personnes.py")
    assert "self._premier_maj_redondant = True" in source
    assert "if self._premier_maj_redondant and IDpersonne is None and presents is None" in source
    assert "super(ListView, self).MAJ" in source


def test_six_onglets_secondaires_sont_differees():
    source = _source("teamworks/Dlg/DLG_Fiche_individuelle.py")
    for attribut in (
        "pageStatut",
        "pageContrats",
        "pagePresences",
        "pageScenarios",
        "pageFrais",
        "pageCandidatures",
    ):
        assert '"%s"' % attribut in source
    assert "pageQuestionnaire = CORE.CTRL_Page_questionnaire.Panel" in source
    assert "wx.personnes.fiche.onglet.chargement" in source


def test_dialogue_personne_appelle_explicitement_le_coeur_sans_super_recursif():
    source = _source("teamworks/Dlg/DLG_Fiche_individuelle.py")
    assert "CORE.Dialog.__init__(self, *args, **kwargs)" in source
    assert "super(Dialog, self).__init__(*args, **kwargs)" not in source


def test_diagnostic_agrege_nombre_requetes_et_temps_sql(monkeypatch):
    path = ROOT / "teamworks/Utils/UTILS_Diagnostic_performance.py"
    spec = importlib.util.spec_from_file_location("diag_perf_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setenv("TEAMWORKS_PERF_DIAG", "1")
    module.reinitialiser_mesures()

    action = module.demarrer_action("action-test")
    module.enregistrer_mesure("sql", "q1", 0.010, {"phase": "execute"})
    module.enregistrer_mesure("sql", "f1", 0.004, {"phase": "fetch"})
    module.enregistrer_mesure("sql", "q2", 0.020, {"phase": "execute"})
    resume = module.terminer_action(action)

    assert resume["details"]["nb_requetes"] == 2
    assert resume["details"]["sql_ms"] == 34.0
    assert resume["details"]["total_ms"] >= 0.0
    assert resume["details"]["python_wx_ms"] >= 0.0
