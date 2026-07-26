from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Utils" / "UTILS_Export.py"


def test_export_text_uses_native_utf8_text_io() -> None:
    source = TARGET.read_text(encoding="iso-8859-15")

    assert 'f.write(texte.encode("utf8"))' not in source
    assert 'open(cheminFichier, "w", encoding="utf-8", newline="")' in source
    assert "fichier.write(texte)" in source


def test_export_source_compiles() -> None:
    source = TARGET.read_text(encoding="iso-8859-15")
    compile(source, str(TARGET), "exec")
