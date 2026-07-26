import importlib.util
from pathlib import Path


MODULE_PATH = Path("tools/migrate_wx_empty_images.py")


def load_module():
    spec = importlib.util.spec_from_file_location("migrate_wx_empty_images", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_migrates_empty_bitmap():
    module = load_module()
    migrated, count = module.migrate_source("bitmap = wx.EmptyBitmap(16, 16)\n")

    assert migrated == "bitmap = wx.Bitmap(16, 16)\n"
    assert count == 1


def test_migrates_empty_image():
    module = load_module()
    migrated, count = module.migrate_source("image = wx.EmptyImage(32, 32)\n")

    assert migrated == "image = wx.Image(32, 32)\n"
    assert count == 1


def test_migrates_both_apis_in_same_source():
    module = load_module()
    source = "bitmap = wx.EmptyBitmap(16, 16)\nimage = wx.EmptyImage(32, 32)\n"

    migrated, count = module.migrate_source(source)

    assert "wx.EmptyBitmap(" not in migrated
    assert "wx.EmptyImage(" not in migrated
    assert migrated.count("wx.Bitmap(") == 1
    assert migrated.count("wx.Image(") == 1
    assert count == 2


def test_does_not_change_similar_names_or_strings():
    module = load_module()
    source = (
        "factory = wx.EmptyBitmapFactory(16, 16)\n"
        "label = 'wx.EmptyImage(32, 32)'\n"
    )

    migrated, count = module.migrate_source(source)

    assert migrated == source
    assert count == 0


def test_migration_is_idempotent():
    module = load_module()
    source = "bitmap = wx.EmptyBitmap(16, 16)\n"

    migrated, first_count = module.migrate_source(source)
    remigrated, second_count = module.migrate_source(migrated)

    assert first_count == 1
    assert second_count == 0
    assert remigrated == migrated
