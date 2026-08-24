from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "teamworks" / "Dlg" / "DLG_Config_sauvegarde.py"


def _source() -> str:
    return SOURCE_PATH.read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_source(), filename=str(SOURCE_PATH))


def test_backup_restore_never_uses_err_as_an_exception_type() -> None:
    handlers = [node for node in ast.walk(_tree()) if isinstance(node, ast.ExceptHandler)]
    assert not any(
        isinstance(handler.type, ast.Name) and handler.type.id == "err"
        for handler in handlers
    )


def test_backup_save_reports_real_exception_instead_of_unknown_error() -> None:
    source = _source()
    assert "with zipfile.ZipFile" in source
    assert "except Exception as err:" in source
    assert 'return str(err)' in source
    assert 'return "Erreur inconnue"' not in source


def test_backup_and_restore_error_messages_use_defined_values() -> None:
    source = _source()
    assert "+ str(etat)" in source
    assert "+ str(err)" in source
    assert ") + err," not in source


def test_restore_stops_after_a_file_write_failure() -> None:
    source = _source()
    fragment = """except Exception as err:\n                    dlg = wx.MessageDialog"""
    start = source.index(fragment)
    guarded_block = source[start : start + 700]
    assert "fichierZip.close()" in guarded_block
    assert "return" in guarded_block
