from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAVE = ROOT / "teamworks" / "Utils" / "UTILS_Sauvegarde.py"
RESTORE = ROOT / "teamworks" / "Dlg" / "DLG_Restauration.py"
CORE = ROOT / "teamworks" / "Teamworks_core.py"


def test_zip_inventory_uses_a_context_manager():
    source = SAVE.read_text(encoding="utf-8")
    assert 'with zipfile.ZipFile(fichier, "r") as fichierZip:' in source
    assert 'return list(fichierZip.namelist())' in source


def test_restore_progress_cleanup_does_not_use_bare_except():
    source = SAVE.read_text(encoding="utf-8")
    assert "dlgprogress = None" in source
    assert "if dlgprogress is not None:" in source
    assert "try:\n        dlgprogress.Destroy()\n    except:" not in source


def test_restored_logical_name_strips_the_whole_tdata_suffix():
    source = RESTORE.read_text(encoding="utf-8")
    assert 'if fichier[-6:] in ("_TDATA", "_tdata")' in source
    assert "nomFichier = fichier[:-6]" in source
    assert "nomFichier = fichier[:-5]" not in source


def test_decrypted_restore_file_has_an_explicit_cleanup_path():
    source = RESTORE.read_text(encoding="utf-8")
    assert 'def NettoyerFichierDecrypteTemporaire(fichier):' in source
    assert 'os.remove(fichier)' in source
    assert 'NettoyerFichierDecrypteTemporaire(fichier)' in source
    core = CORE.read_text(encoding="utf-8")
    assert 'finally:' in core
    assert 'DLG_Restauration.NettoyerFichierDecrypteTemporaire(fichier)' in core


def test_restore_sources_still_parse_after_cleanup_hardening():
    ast.parse(SAVE.read_text(encoding="utf-8"), filename=str(SAVE))
    ast.parse(RESTORE.read_text(encoding="utf-8"), filename=str(RESTORE))
    ast.parse(CORE.read_text(encoding="utf-8"), filename=str(CORE))
