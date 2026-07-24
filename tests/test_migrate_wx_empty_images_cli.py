import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/migrate_wx_empty_images.py")


def run_cli(*args: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_check_reports_legacy_wx_image_api(tmp_path):
    source = tmp_path / "sample.py"
    source.write_text("bitmap = wx.EmptyBitmap(16, 16)\n", encoding="utf-8")

    result = run_cli("--check", "--path", str(source))

    assert result.returncode == 1
    assert "1 remplacement(s)" in result.stdout


def test_write_applies_migration_and_second_check_passes(tmp_path):
    source = tmp_path / "sample.py"
    source.write_text(
        "bitmap = wx.EmptyBitmap(16, 16)\n"
        "image = wx.EmptyImage(32, 32)\n",
        encoding="utf-8",
    )

    write_result = run_cli("--write", "--path", str(source))
    check_result = run_cli("--check", "--path", str(source))

    assert write_result.returncode == 0
    assert "2 remplacement(s)" in write_result.stdout
    assert source.read_text(encoding="utf-8") == (
        "bitmap = wx.Bitmap(16, 16)\n"
        "image = wx.Image(32, 32)\n"
    )
    assert check_result.returncode == 0
    assert "Total: 0 remplacement(s)" in check_result.stdout
