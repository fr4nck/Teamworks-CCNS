import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRESENCES = ROOT / "teamworks/Ctrl/CTRL_Presences.py"
DIAGNOSTIC = ROOT / "teamworks/Utils/UTILS_Diagnostic_performance.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_fichiers_instrumentation_presences_compilent():
    for path in (PRESENCES, DIAGNOSTIC):
        compile(_source(path), str(path), "exec")


def test_majpanel_presences_est_decoupe_en_actions_mesurables():
    source = _source(PRESENCES)
    for action in (
        "wx.presences.majpanel",
        "wx.presences.initialisation",
        "wx.presences.planning.preparation",
        "wx.presences.planning.maj",
        "wx.presences.planning.recherche_presents",
        "wx.presences.planning.reinit",
        "wx.presences.planning.categories",
        "wx.presences.planning.affichage",
        "wx.presences.personnes.maj",
        "wx.presences.legendes.maj",
        "wx.presences.calendrier.maj",
    ):
        assert '"%s"' % action in source

    assert "DiagnosticPerformance.installer_instrumentation_sql(GestionDB)" in source
    assert source.index("installer_instrumentation_sql") < source.index("self.InitPage()")


def test_signature_sql_ne_conserve_ni_valeurs_ni_requete_complete():
    spec = importlib.util.spec_from_file_location("diag_presences_test", DIAGNOSTIC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    signature = module._signature_requete(
        "SELECT nom FROM presences WHERE IDpersonne=123 AND nom='SECRET'"
    )
    assert signature == "select:presences"
    assert "123" not in signature
    assert "SECRET" not in signature
    assert '"requete"' not in _source(DIAGNOSTIC)


def test_journal_perf_persiste_uniquement_les_metriques_agregees(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("diag_presences_log_test", DIAGNOSTIC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    journal = tmp_path / "performance.jsonl"
    monkeypatch.setenv("TEAMWORKS_PERF_DIAG", "1")
    monkeypatch.setenv("TEAMWORKS_PERF_LOG", str(journal))
    module.reinitialiser_mesures()

    action = module.demarrer_action(
        "wx.presences.majpanel",
        {"IDpersonne": 123, "texte": "SECRET"},
    )
    module.enregistrer_mesure("sql", "q", 0.010, {"phase": "execute"})
    module.enregistrer_mesure("sql", "f", 0.004, {"phase": "fetch"})
    module.enregistrer_mesure("connexion", "c", 0.002, {})
    resume = module.terminer_action(action)

    assert resume["details"]["nb_requetes"] == 1
    ligne = journal.read_text(encoding="utf-8").strip()
    donnees = json.loads(ligne)
    assert donnees["nom"] == "wx.presences.majpanel"
    assert donnees["details"]["nb_requetes"] == 1
    assert donnees["details"]["sql_ms"] == 14.0
    assert donnees["details"]["connexion_ms"] == 2.0
    assert set(donnees["details"]) == {
        "nb_requetes",
        "sql_ms",
        "connexion_ms",
        "io_ms",
        "python_wx_ms",
        "total_ms",
    }
    assert "IDpersonne" not in donnees["details"]
    assert "texte" not in donnees["details"]
    assert "SECRET" not in ligne
