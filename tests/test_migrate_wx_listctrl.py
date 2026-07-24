from tools.migrate_wx_listctrl import migrate_source


def test_migrate_insert_string_item():
    source = "self.list_ctrl.InsertStringItem(index, label)\n"

    migrated, replacements = migrate_source(source)

    assert migrated == "self.list_ctrl.InsertItem(index, label)\n"
    assert replacements == 1


def test_migrate_six_maxsize_adds_sys_import():
    source = "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\nimport six\nLIMIT = six.MAXSIZE\n"

    migrated, replacements = migrate_source(source)

    assert "import sys\nimport six" in migrated
    assert "LIMIT = sys.maxsize" in migrated
    assert replacements == 1


def test_migration_is_idempotent():
    source = "import sys\nLIMIT = sys.maxsize\nself.list_ctrl.InsertItem(index, label)\n"

    migrated, replacements = migrate_source(source)

    assert migrated == source
    assert replacements == 0


def test_existing_sys_import_is_not_duplicated():
    source = "import sys\nimport six\nLIMIT = six.MAXSIZE\n"

    migrated, replacements = migrate_source(source)

    assert migrated.count("import sys") == 1
    assert "LIMIT = sys.maxsize" in migrated
    assert replacements == 1
