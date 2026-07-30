import datetime
import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "teamworks" / "Utils" / "UTILS_Dates.py"

utils_package = types.ModuleType("Utils")
utils_package.__path__ = []
translation_module = types.ModuleType("Utils.UTILS_Traduction")
translation_module._ = lambda value: value
sys.modules.setdefault("Utils", utils_package)
sys.modules["Utils.UTILS_Traduction"] = translation_module

spec = importlib.util.spec_from_file_location("UTILS_Dates_under_test", MODULE_PATH)
UTILS_Dates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(UTILS_Dates)


def test_date_parser_accepts_historical_formats():
    expected = datetime.date(2020, 5, 12)
    assert UTILS_Dates.DateEnDateDD("2020-05-12") == expected
    assert UTILS_Dates.DateEnDateDD("2020-5-12") == expected
    assert UTILS_Dates.DateEnDateDD("12/05/2020") == expected
    assert UTILS_Dates.DateEnDateDD("12-05-2020") == expected
    assert UTILS_Dates.DateEnDateDD("2020-05-12 00:00:00") == expected
    assert UTILS_Dates.DateEnDateDD(datetime.datetime(2020, 5, 12, 9, 30)) == expected


def test_invalid_date_never_crashes():
    assert UTILS_Dates.DateEnDateDD(None) is None
    assert UTILS_Dates.DateEnDateDD("") is None
    assert UTILS_Dates.DateEnDateDD("2020-5-") is None
    assert UTILS_Dates.DateEngFr("2020-5-") == ""


def test_formatters_are_canonical():
    assert UTILS_Dates.DateEngFr("2020-5-12") == "12/05/2020"
    assert UTILS_Dates.DateFrEng("12/05/2020") == "2020-05-12"


def test_manual_date_string_slicing_cannot_return():
    forbidden_fragments = ("dateStr[:4]", "dateStr[5:7]", "dateStr[8:10]")
    offenders = []

    for path in (ROOT / "teamworks").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for fragment in forbidden_fragments:
            if fragment in source:
                offenders.append(f"{path.relative_to(ROOT)}: {fragment}")

    assert offenders == []
