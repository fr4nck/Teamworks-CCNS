from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "LANCER_TEAMWORKS_WINDOWS.cmd"


def test_windows_launcher_targets_python311_and_validated_entrypoint():
    source = LAUNCHER.read_text(encoding="utf-8")

    assert 'py -3.11 -m venv .venv' in source
    assert 'requirements\\python311-core.txt' in source
    assert '".venv\\Scripts\\python.exe" run_teamworks.py' in source


def test_windows_launcher_stops_on_preparation_errors():
    source = LAUNCHER.read_text(encoding="utf-8")

    assert 'if errorlevel 1 goto :error' in source
    assert ':error' in source
    assert 'exit /b 1' in source
