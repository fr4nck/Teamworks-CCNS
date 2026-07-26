import importlib.util
from pathlib import Path


MIGRATOR_PATH = Path("tools/migrate_wx_setstringitem.py")
OBJECT_LIST_VIEW_PATH = Path("teamworks/ObjectListView/ObjectListView.py")

SPEC = importlib.util.spec_from_file_location(
    "migrate_wx_setstringitem",
    MIGRATOR_PATH,
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_objectlistview_no_longer_contains_setstringitem():
    source = OBJECT_LIST_VIEW_PATH.read_text(encoding="utf-8")
    migrated, count = MODULE.migrate_source(source)

    assert count == 0
    assert ".SetStringItem(" not in source
    assert ".SetItem(" in source
    assert migrated == source


def test_objectlistview_setstringitem_migration_is_idempotent():
    source = OBJECT_LIST_VIEW_PATH.read_text(encoding="utf-8")
    migrated, first_count = MODULE.migrate_source(source)
    migrated_again, second_count = MODULE.migrate_source(migrated)

    assert first_count == 0
    assert second_count == 0
    assert migrated_again == migrated == source
