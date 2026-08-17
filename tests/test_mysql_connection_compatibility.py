import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "teamworks" / "Utils" / "UTILS_MySQL.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("utils_mysql_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_legacy_server_connection_uses_pure_python_without_ssl_by_default():
    module = _load_module()

    options = module.ConstruireOptionsConnexion(
        "serveur.local", "teamworks", "secret", 3306, {}
    )

    assert options["use_pure"] is True
    assert options["ssl_disabled"] is True
    assert options["charset"] == "utf8"
    assert options["connection_timeout"] == 10
    assert options["passwd"] == "secret"
    assert "ssl_ca" not in options


def test_configured_certificates_keep_tls_enabled():
    module = _load_module()

    options = module.ConstruireOptionsConnexion(
        "db", "user", "secret", "3307",
        {"ca": "ca.pem", "key": "key.pem", "cert": "cert.pem"},
    )

    assert options["ssl_ca"] == "ca.pem"
    assert options["ssl_key"] == "key.pem"
    assert options["ssl_cert"] == "cert.pem"
    assert "ssl_disabled" not in options


def test_diagnostic_is_detailed_and_never_contains_credentials():
    module = _load_module()

    class ConnectorError(RuntimeError):
        errno = 1045
        sqlstate = "28000"

    diagnostic = module.FormaterDiagnosticConnexion(
        ConnectorError("Access denied"), "db.local", 3306,
        "mysql.connector", "9.5.0",
    )

    assert "ConnectorError: Access denied" in diagnostic
    assert "mysql.connector 9.5.0" in diagnostic
    assert "db.local:3306" in diagnostic
    assert "Code MySQL : 1045" in diagnostic
    assert "SQLSTATE : 28000" in diagnostic
    assert "secret" not in diagnostic


def test_opaque_pyinstaller_error_gets_an_actionable_hint():
    module = _load_module()
    diagnostic = module.FormaterDiagnosticConnexion(
        RuntimeError("Failed raising error."), "db", 3306,
        "mysql.connector", "9.5.0",
    )

    assert "artefact Windows" in diagnostic
    assert "manifeste" in diagnostic


def test_identical_connection_diagnostic_is_emitted_only_once_per_session():
    module = _load_module()
    module.ReinitialiserDiagnosticsConnexion()

    diagnostic = "Connexion MySQL impossible sur serveur.local:3306"

    assert module.ConsommerDiagnosticConnexion(diagnostic) == diagnostic
    assert module.ConsommerDiagnosticConnexion(diagnostic) is None
    assert module.ConsommerDiagnosticConnexion("Autre erreur") == "Autre erreur"


def test_windows_build_collects_the_complete_mysql_connector_package():
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "'--collect-all', 'mysql.connector'" in workflow
    assert "'--hidden-import', 'mysql.connector'" not in workflow
