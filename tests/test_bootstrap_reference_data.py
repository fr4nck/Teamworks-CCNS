from application.bootstrap.seed_reference_data import (
    build_default_ccns_classifications,
    build_default_salary_grid_2026,
    build_default_time_natures,
    build_default_roles_seed,
)


def test_default_ccns_classifications_exist():
    classifications = build_default_ccns_classifications()
    assert len(classifications) >= 9
    assert any(item.code == "G7" for item in classifications)


def test_default_salary_grid_contains_g3_and_g7():
    grid, lines = build_default_salary_grid_2026()
    assert grid.code == "CCNS-2026"
    assert any(line.classification_code == "G3" for line in lines)
    assert any(line.classification_code == "G7" for line in lines)


def test_default_time_natures_exist():
    natures = build_default_time_natures()
    assert any(item["code"] == "PREPARATION" for item in natures)


def test_default_roles_seed_exists():
    roles = build_default_roles_seed()
    assert len(roles) >= 6
