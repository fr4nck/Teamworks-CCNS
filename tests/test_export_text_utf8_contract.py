from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Utils" / "UTILS_Export.py"
LIST_EXPORT_SHELLS = (
    ROOT / "teamworks" / "Ol" / "OL_candidats.py",
    ROOT / "teamworks" / "Ol" / "OL_candidatures.py",
    ROOT / "teamworks" / "Ol" / "OL_Destinataires_emails.py",
    ROOT / "teamworks" / "Ol" / "OL_emplois.py",
    ROOT / "teamworks" / "Ol" / "OL_entretiens.py",
)


def _implementation_path(shell: Path) -> Path:
    core = shell.with_name(f"{shell.stem}_core.py")
    return core if core.exists() else shell


def test_export_text_uses_native_utf8_text_io() -> None:
    source = TARGET.read_text(encoding="utf-8")

    assert 'f.write(texte.encode("utf8"))' not in source
    assert 'open(cheminFichier, "w", encoding="utf-8", newline="")' in source
    assert "fichier.write(texte)" in source


def test_export_source_compiles() -> None:
    source = TARGET.read_text(encoding="utf-8")
    compile(source, str(TARGET), "exec")


def test_legacy_list_exports_now_write_utf8_text() -> None:
    for shell in LIST_EXPORT_SHELLS:
        shell_source = shell.read_text(encoding="utf-8")
        compile(shell_source, str(shell), "exec")

        implementation = _implementation_path(shell)
        source = implementation.read_text(encoding="utf-8")
        assert '.encode("iso-8859-15")' not in source
        assert 'open(cheminFichier, "w", encoding="utf-8", newline="")' in source
        compile(source, str(implementation), "exec")
