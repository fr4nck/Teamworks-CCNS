from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "teamworks" / "Dlg" / "DLG_Scenario.py"
DURATION = ROOT / "teamworks" / "Utils" / "UTILS_Duration.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_scenario_presence_uses_clock_time_adapter_in_both_paths():
    source = _source(SCENARIO)
    assert "from Utils.UTILS_Duration import duree_presence_wx" in source
    assert source.count("duree_presence_wx(heure_debut, heure_fin") == 2
    assert 'OperationHeures("+" + heure_fin' not in source


def test_presence_adapter_keeps_raw_difference_without_implicit_overnight():
    source = _source(DURATION)
    assert "allow_overnight=False" in source
    assert "calculate_time_difference(" in source
