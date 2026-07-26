from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "run_teamworks.py"


def test_root_launcher_exposes_modern_and_legacy_import_roots():
    source = LAUNCHER.read_text(encoding="utf-8")

    assert "ROOT = Path(__file__).resolve().parent" in source
    assert 'TEAMWORKS_DIR = ROOT / "teamworks"' in source
    assert "sys.path.insert(0, str(ROOT))" in source
    assert "sys.path.insert(0, str(TEAMWORKS_DIR))" in source


def test_root_launcher_executes_historical_entrypoint_as_main():
    source = LAUNCHER.read_text(encoding="utf-8")

    assert "runpy.run_path" in source
    assert 'run_name="__main__"' in source
    assert 'TEAMWORKS_DIR / "Teamworks.py"' in source
