from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "teamworks" / "Dlg" / "DLG_Scenario.py"
DURATION = ROOT / "teamworks" / "Utils" / "UTILS_Duration.py"

sys.path.insert(0, str(ROOT / "teamworks"))
from Utils.UTILS_Duration import duree_presence_wx


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


def test_presence_positive_duration():
    valeur, resultat = duree_presence_wx("08:00", "12:00")
    assert resultat.ok is True
    assert resultat.value_minutes == 240
    assert valeur == "+4:00"


def test_presence_negative_duration_is_valid():
    valeur, resultat = duree_presence_wx("09:00", "08:30")
    assert resultat.ok is True
    assert resultat.value_minutes == -30
    assert valeur == "-0:30"


def test_presence_equal_times_is_zero_not_twenty_four_hours():
    valeur, resultat = duree_presence_wx("08:00", "08:00")
    assert resultat.ok is True
    assert resultat.value_minutes == 0
    assert valeur == "+0:00"


def test_presence_does_not_infer_overnight():
    valeur, resultat = duree_presence_wx("22:00", "02:00")
    assert resultat.ok is True
    assert resultat.value_minutes == -20 * 60
    assert valeur == "-20:00"


def test_presence_missing_time_returns_structured_error():
    valeur, resultat = duree_presence_wx(None, "12:00")
    assert valeur is None
    assert resultat.ok is False
    assert resultat.error is not None
    assert resultat.error.code == "MISSING_TIME"


def test_presence_malformed_time_returns_structured_error():
    valeur, resultat = duree_presence_wx("8h30", "12:00")
    assert valeur is None
    assert resultat.ok is False
    assert resultat.error is not None
    assert resultat.error.code == "INVALID_TIME_FORMAT"


def test_presence_out_of_range_time_returns_structured_error():
    valeur, resultat = duree_presence_wx("08:00", "24:00")
    assert valeur is None
    assert resultat.ok is False
    assert resultat.error is not None
    assert resultat.error.code == "INVALID_TIME_VALUE"
