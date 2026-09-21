from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_qt_vanilla_mysql_terrain.ps1"
GO_NO_GO = ROOT / "docs" / "GO_NO_GO_QT_VANILLA_0.1.md"
RECIPE = ROOT / "docs" / "RECETTE_QT_VANILLA_0.1_MYSQL_REEL.md"
PV = ROOT / "docs" / "PV_RECETTE_QT_VANILLA_0.1_MYSQL.md"


def test_terrain_launcher_has_safe_actions_and_database_guard():
    source = SCRIPT.read_text(encoding="utf-8")

    assert '[ValidateSet("Start", "Finish", "Performance")]' in source
    assert "_qt_vanilla_recette" in source
    assert "^[0-9a-fA-F]{40}$" in source
    assert "mysql-before.json" in source
    assert "mysql-after.json" in source
    assert "mysql-compare.json" in source
    assert "performance-summary.json" in source


def test_terrain_launcher_never_accepts_password_argument():
    source = SCRIPT.read_text(encoding="utf-8")

    assert "Read-Host" in source
    assert "-AsSecureString" in source
    assert "TEAMWORKS_MYSQL_PASSWORD" in source
    assert "Remove-Item Env:TEAMWORKS_MYSQL_PASSWORD" in source

    lowered = source.lower()
    assert "[string]$password" not in lowered
    assert "--password" not in lowered


def test_terrain_launcher_reuses_qualified_evidence_collector():
    source = SCRIPT.read_text(encoding="utf-8")

    assert "tools/collect_qt_vanilla_mysql_evidence.py" in source
    assert '"snapshot"' in source
    assert '"compare"' in source
    assert '"performance"' in source


def test_go_no_go_has_three_explicit_terminal_states():
    text = GO_NO_GO.read_text(encoding="utf-8")

    assert "GO\nNO-GO\nNON QUALIFIEE" in text
    assert "si preuve obligatoire manquante -> NON QUALIFIEE" in text
    assert "sinon si un bloqueur existe       -> NO-GO" in text
    assert "sinon                             -> GO" in text


def test_go_no_go_forbids_waivers_for_data_and_mysql_safety():
    text = GO_NO_GO.read_text(encoding="utf-8")

    for item in (
        "corruption/perte de données",
        "erreur transactionnelle",
        "incompatibilité MySQL",
        "mutation de schéma",
        "fuite de connexion",
        "fuite de données personnelles",
        "divergence de SHA",
    ):
        assert item in text


def test_recipe_and_pv_reference_go_no_go_and_terrain_launcher():
    recipe = RECIPE.read_text(encoding="utf-8")
    pv = PV.read_text(encoding="utf-8")

    assert "GO_NO_GO_QT_VANILLA_0.1.md" in recipe
    assert "run_qt_vanilla_mysql_terrain.ps1" in recipe
    assert "GO / NO-GO / NON QUALIFIEE" in pv
