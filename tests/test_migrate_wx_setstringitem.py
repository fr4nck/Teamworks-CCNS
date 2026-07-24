import importlib.util
from pathlib import Path


MODULE_PATH = Path("tools/migrate_wx_setstringitem.py")
SPEC = importlib.util.spec_from_file_location("migrate_wx_setstringitem", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_replaces_setstringitem_call():
    source = 'self.SetStringItem(index, column, label)\n'

    migrated, count = MODULE.migrate_source(source)

    assert count == 1
    assert migrated == 'self.SetItem(index, column, label)\n'


def test_replaces_multiple_calls():
    source = (
        'self.SetStringItem(0, 1, "A")\n'
        'other.SetStringItem(1, 2, "B", image)\n'
    )

    migrated, count = MODULE.migrate_source(source)

    assert count == 2
    assert ".SetStringItem(" not in migrated
    assert migrated.count(".SetItem(") == 2


def test_does_not_replace_plain_text_or_different_method_names():
    source = (
        'message = "self.SetStringItem(index, column, label)"\n'
        'self.SetStringItemLegacy(index, column, label)\n'
    )

    migrated, count = MODULE.migrate_source(source)

    assert count == 1
    assert '"self.SetItem(index, column, label)"' in migrated
    assert "SetStringItemLegacy" in migrated


def test_is_idempotent_after_migration():
    migrated, count = MODULE.migrate_source('self.SetStringItem(0, 1, "A")\n')
    migrated_again, second_count = MODULE.migrate_source(migrated)

    assert count == 1
    assert second_count == 0
    assert migrated_again == migrated
