from pathlib import Path

from tools.functional_db_roundtrip import run


def test_functional_db_roundtrip(tmp_path: Path) -> None:
    result = run(tmp_path)

    assert result["status"] == "ok"
    assert result["backup_integrity"] == "ok"
    assert set(result["initial_integrity"].values()) == {"ok"}
    assert set(result["final_integrity"].values()) == {"ok"}
    assert result["roundtrip"]["integrity"] == "ok"

    assert (tmp_path / "Exemple_TDATA.dat").is_file()
    assert (tmp_path / "Exemple_TDOCUMENTS.dat").is_file()
    assert (tmp_path / "Exemple_TPHOTOS.dat").is_file()
    assert (tmp_path / "Sauvegarde_Exemple_TDATA.dat").is_file()
