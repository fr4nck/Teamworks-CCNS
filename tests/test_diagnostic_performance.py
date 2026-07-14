from teamworks.Utils import UTILS_Diagnostic_performance as diag


def setup_function(_function):
    diag.reinitialiser_mesures()


def test_diagnostic_desactive_par_defaut(monkeypatch):
    monkeypatch.delenv("TEAMWORKS_PERF_DIAG", raising=False)

    with diag.mesurer("sql", "requete_test"):
        pass
    diag.enregistrer_mesure("widget", "maj", 0.1)

    assert diag.obtenir_mesures() == []


def test_diagnostic_active_par_variable_environnement(monkeypatch):
    monkeypatch.setenv("TEAMWORKS_PERF_DIAG", "1")

    with diag.mesurer("transformation_python", "calcul_test", {"taille": 3}):
        somme = sum([1, 2, 3])

    mesures = diag.obtenir_mesures()
    assert somme == 6
    assert len(mesures) == 1
    assert mesures[0]["categorie"] == "transformation_python"
    assert mesures[0]["nom"] == "calcul_test"
    assert mesures[0]["details"] == {"taille": 3}
    assert mesures[0]["duree"] >= 0.0


def test_reinitialisation_des_mesures(monkeypatch):
    monkeypatch.setenv("TEAMWORKS_PERF_DIAG", "oui")
    diag.enregistrer_mesure("connexion", "ouverture", 0.01)

    diag.reinitialiser_mesures()

    assert diag.obtenir_mesures() == []
