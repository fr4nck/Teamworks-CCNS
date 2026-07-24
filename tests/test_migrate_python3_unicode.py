import ast
import importlib.util
from pathlib import Path


MODULE_PATH = Path("tools/migrate_python3_unicode.py")
TARGET_DIALOG = Path("teamworks/Dlg/DLG_Saisie_utilisateur_reseau.py")
SPEC = importlib.util.spec_from_file_location("migrate_python3_unicode", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_replaces_direct_unicode_call():
    migrated, count = MODULE.migrate_source("value = unicode(label)\n")

    assert count == 1
    assert "value = str(label)" in migrated
    ast.parse(migrated)


def test_does_not_replace_string_or_attribute_names():
    source = 'message = "unicode(value)"\ncodec.unicode(value)\n'
    migrated, count = MODULE.migrate_source(source)

    assert count == 0
    assert migrated == source


def test_replaces_nested_direct_calls():
    migrated, count = MODULE.migrate_source("result = unicode(unicode(value))\n")

    assert count == 2
    assert "result = str(str(value))" in migrated


def test_is_idempotent_after_migration():
    migrated, count = MODULE.migrate_source("value = unicode(label)\n")
    migrated_again, second_count = MODULE.migrate_source(migrated)

    assert count == 1
    assert second_count == 0
    assert migrated_again == migrated


def test_network_user_dialog_no_longer_calls_unicode():
    source = TARGET_DIALOG.read_text(encoding="utf-8")
    tree = ast.parse(source)

    unicode_calls = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "unicode"
    ]

    assert unicode_calls == []
