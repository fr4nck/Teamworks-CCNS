from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "teamworks/Utils/UTILS_Qualifications_091g.py"
ENTRYPOINT = ROOT / "teamworks/Teamworks.py"


def test_qualifications_patch_never_reparses_piece_dates_by_slicing():
    source = PATCH.read_text(encoding="utf-8")
    assert "UTILS_Dates.DateEnDateDD(date_fin)" in source
    assert 'etat = "Invalide"' in source
    assert 'return "Date invalide"' in source
    assert 'int(date_fin[:4])' not in source
    assert 'reste.index("day")' not in source


def test_invalid_piece_date_is_not_rewritten_or_treated_as_unlimited():
    source = PATCH.read_text(encoding="utf-8")
    invalid_branch = source.split("if date_fin_dd is None:", 1)[1].split(
        "elif date_fin_dd < date_jour:", 1
    )[0]
    assert 'etat = "Invalide"' in invalid_branch
    assert "2999" not in invalid_branch
    assert "ReqMAJ" not in source
    assert "ReqInsert" not in source


def test_runtime_installs_qualifications_patch_before_user_navigation():
    source = ENTRYPOINT.read_text(encoding="utf-8")
    assert "from Utils import UTILS_Qualifications_091g" in source
    assert "UTILS_Qualifications_091g.install()" in source
    assert source.index("UTILS_Qualifications_091g.install()") < source.index(
        "class Toolbook"
    )
