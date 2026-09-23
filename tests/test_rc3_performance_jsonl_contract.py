from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_jsonl_expose_les_metriques_demandees():
    source = (ROOT / "teamworks/Utils/UTILS_Diagnostic_performance.py").read_text(encoding="utf-8")
    for cle in (
        "total_ms",
        "nb_requetes",
        "connexions_physiques",
        "connexions_reutilisees",
        "connexion_ms",
        "sql_ms",
        "python_wx_ms",
    ):
        assert '"%s"' % cle in source
    assert 'categorie == "connexion"' in source
    assert 'categorie == "connexion_reutilisee"' in source
    assert "enregistrer_reutilisation_connexion" in source
