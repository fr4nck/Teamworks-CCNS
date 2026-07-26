import importlib.util
from pathlib import Path


MODULE_PATH = Path("tools/migrate_dlg_publiposteur_choix_six.py")
SPEC = importlib.util.spec_from_file_location("migrate_dlg_publiposteur_choix_six", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_migrates_only_expected_six_constructs():
    source = (
        "# -*- coding: iso-8859-15 -*-\n"
        "import six\n"
        "first = six.text_type(donnees[0])\n"
        "other = six.text_type(donnees[x])\n"
    )

    migrated, changes = MODULE.migrate_source(source)

    assert changes == 4
    assert "coding: utf-8" in migrated
    assert "import six" not in migrated
    assert "six.text_type" not in migrated
    assert "str(donnees[0])" in migrated
    assert "str(donnees[x])" in migrated


def test_migration_is_idempotent():
    source = (
        "# -*- coding: utf-8 -*-\n"
        "first = str(donnees[0])\n"
        "other = str(donnees[x])\n"
    )

    migrated, changes = MODULE.migrate_source(source)

    assert changes == 0
    assert migrated == source
