import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE_RUNTIME = ROOT / "tools" / "smoke_runtime.py"


def _charger_module():
    spec = importlib.util.spec_from_file_location("smoke_runtime_sql_guard_test", SMOKE_RUNTIME)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_erreurs_sql_historiques_sont_detectees():
    module = _charger_module()

    assert module._contient_erreur_sql("Requete SQL incorrecte :\nSELECT 1")
    assert module._contient_erreur_sql("Requete sql d'INSERT incorrecte :")
    assert module._contient_erreur_sql("Erreur dans creation table: doublon")
    assert not module._contient_erreur_sql("TEAMWORKS_SMOKE_PERSON_DIALOG_READY")


def test_code_erreur_sql_est_distinct_du_timeout():
    module = _charger_module()

    assert module.SQL_ERROR_RETURN_CODE == 125
    assert module.SQL_ERROR_RETURN_CODE != module.TIMEOUT_RETURN_CODE
