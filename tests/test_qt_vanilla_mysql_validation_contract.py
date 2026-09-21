from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs" / "MATRICE_VALIDATION_QT_VANILLA_0.1_MYSQL.md"
THRESHOLDS = ROOT / "docs" / "SEUILS_PERFORMANCE_QT_VANILLA_0.1.md"
PV = ROOT / "docs" / "PV_RECETTE_QT_VANILLA_0.1_MYSQL.md"
RECIPE = ROOT / "docs" / "RECETTE_QT_VANILLA_0.1_MYSQL_REEL.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_mysql_validation_documents_are_cross_linked():
    recipe = _read(RECIPE)

    for name in (
        "MATRICE_VALIDATION_QT_VANILLA_0.1_MYSQL.md",
        "SEUILS_PERFORMANCE_QT_VANILLA_0.1.md",
        "PV_RECETTE_QT_VANILLA_0.1_MYSQL.md",
    ):
        assert name in recipe


def test_compatibility_and_integrity_ids_exist_in_matrix_and_pv():
    matrix = _read(MATRIX)
    pv = _read(PV)

    for prefix, maximum in (("C", 30), ("I", 20)):
        for number in range(1, maximum + 1):
            test_id = f"{prefix}-{number:02d}"
            assert test_id in matrix
            assert test_id in pv


def test_performance_ids_exist_in_matrix_thresholds_and_pv():
    matrix = _read(MATRIX)
    thresholds = _read(THRESHOLDS)
    pv = _read(PV)

    for number in range(1, 15):
        test_id = f"P-{number:02d}"
        assert test_id in matrix
        assert test_id in thresholds
        assert test_id in pv


def test_release_verdicts_are_explicit():
    matrix = _read(MATRIX)
    pv = _read(PV)

    for verdict in (
        "COMPATIBILITE MYSQL",
        "INTEGRITE DONNEES",
        "PERFORMANCE",
    ):
        assert verdict in matrix
        assert verdict in pv

    assert "VERDICT GLOBAL" in pv
    assert "QUALIFIEE / BLOQUEE / NON QUALIFIEE" in pv


def test_performance_contract_contains_hard_failure_thresholds():
    thresholds = _read(THRESHOLDS)

    assert "≤ 1,20" in thresholds
    assert "> 1,50" in thresholds
    assert "> 50 %" in thresholds
    assert "> 250 MiB" in thresholds
    assert "retour au niveau initial dans les 10 secondes" in thresholds
    assert "≥ 80 %" in thresholds
