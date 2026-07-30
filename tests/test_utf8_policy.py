from pathlib import Path

from scripts import check_utf8


ROOT = Path(__file__).resolve().parents[1]
LEGACY_RUNTIME_BOUNDARIES = {
    "teamworks/Utils/UTILS_Encodage.py",
    "teamworks/Utils/UTILS_Theme.py",
}


def test_all_tracked_text_files_follow_utf8_policy() -> None:
    errors = [
        error
        for path in check_utf8.tracked_files()
        for error in check_utf8.audit_file(path)
    ]
    assert errors == []


def test_legacy_encoding_names_stay_at_external_import_boundaries() -> None:
    offenders = set()
    for path in (ROOT / "teamworks").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if "iso-8859-15" in source.lower() or "cp1252" in source.lower():
            offenders.add(path.relative_to(ROOT).as_posix())

    assert offenders == LEGACY_RUNTIME_BOUNDARIES
