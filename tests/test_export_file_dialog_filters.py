from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ROOT / "teamworks" / "Utils" / "UTILS_Excel.py",
    ROOT / "teamworks" / "Ol" / "OL_personnes.py",
    ROOT / "teamworks" / "Ol" / "OL_candidatures.py",
    ROOT / "teamworks" / "Ol" / "OL_candidats.py",
    ROOT / "teamworks" / "Ol" / "OL_entretiens.py",
    ROOT / "teamworks" / "Ol" / "OL_emplois.py",
)


def test_two_choice_export_dialogs_use_a_valid_filter_index():
    offenders = []

    for path in TARGETS:
        source = path.read_text(encoding="utf-8")
        if "SetFilterIndex(2)" in source:
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []


def test_excel_export_defaults_to_the_xlsx_filter():
    source = TARGETS[0].read_text(encoding="utf-8")

    assert 'wildcard = "Fichiers Excel (*.xlsx)|*.xlsx|' in source
    assert "dlg.SetFilterIndex(0)" in source
