from domain.convention.minimum_type import MinimumType

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


def test_default_salary_grid_uses_official_ccns_minima_2026():
    _grid, lines = build_default_salary_grid_2026()
    by_code = {line.classification_code: line for line in lines}
    expected = {
        "G1": (MinimumType.MONTHLY, 1848.42),
        "G2": (MinimumType.MONTHLY, 1885.14),
        "G3": (MinimumType.MONTHLY, 1997.87),
        "G4": (MinimumType.MONTHLY, 2099.37),
        "G5": (MinimumType.MONTHLY, 2333.99),
        "G6": (MinimumType.MONTHLY, 2865.97),
        "G7": (MinimumType.ANNUAL, 40597.94),
        "G8": (MinimumType.ANNUAL, 46833.81),
    }

    assert set(expected).issubset(by_code)
    for code, (minimum_type, amount) in expected.items():
        line = by_code[code]
        assert line.minimum_type == minimum_type
        assert line.amount == amount
        assert line.unit == "EUR"


def test_default_time_natures_exist():
    natures = build_default_time_natures()
    assert any(item["code"] == "PREPARATION" for item in natures)


def test_default_roles_seed_exists():
    roles = build_default_roles_seed()
    assert len(roles) >= 6
