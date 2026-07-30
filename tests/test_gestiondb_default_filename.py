from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "GestionDB.py"


def test_db_resolves_current_teamworks_file_before_suffix_handling() -> None:
    source = TARGET.read_text(encoding="utf-8")
    block = (
        '        if self.nomFichier == "":\n'
        '            self.nomFichier = self.GetNomFichierDefaut()\n'
    )

    assert source.count(block) == 1
    assert source.index("self.nomFichier = nomFichier") < source.index(block)
    assert source.index(block) < source.index("if MODE_TEAMWORKS == True")
    assert "def GetNomFichierDefaut(self):" in source


def test_db_default_filename_source_still_compiles() -> None:
    source = TARGET.read_text(encoding="utf-8")
    compile(source, str(TARGET), "exec")
