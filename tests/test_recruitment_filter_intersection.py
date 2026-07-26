from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Ol" / "OL_candidatures.py"


def test_recruitment_filter_intersection_is_explicit_and_deterministic() -> None:
    source = TARGET.read_text(encoding="iso-8859-15")

    assert 'exec("listeID=%s" % texteFonction)' not in source
    assert "set.intersection(*(set(liste) for liste in listeListes))" in source


def test_recruitment_list_source_compiles() -> None:
    source = TARGET.read_text(encoding="iso-8859-15")
    compile(source, str(TARGET), "exec")
