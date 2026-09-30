import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
VERSION_UTIL = ROOT / "teamworks" / "Utils" / "UTILS_Version.py"


def _charger_module():
    spec = importlib.util.spec_from_file_location("utils_version_rc3_test", VERSION_UTIL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_versions_numeriques_historiques_restent_inchangees():
    module = _charger_module()

    assert module.ConvertirTuple("0.9.2") == (0, 9, 2)
    assert module.ConvertirTuple("2.13.1.4") == (2, 13, 1, 4)
    assert module.ConvertirTuple([1, 0, 5, 2]) == (1, 0, 5, 2)
    assert module.ConvertirTuple((1, 0, 5, 2)) == (1, 0, 5, 2)


def test_suffixes_de_preversion_nentrent_pas_dans_la_version_de_schema():
    module = _charger_module()

    assert module.ConvertirTuple("0.9.2-rc3") == (0, 9, 2)
    assert module.ConvertirTuple("0.9.2-rc1") == (0, 9, 2)
    assert module.ConvertirTuple("0.9.1f") == (0, 9, 1)


def test_version_sans_prefixe_numerique_reste_invalide():
    module = _charger_module()

    with pytest.raises(ValueError):
        module.ConvertirTuple("")
    with pytest.raises(ValueError):
        module.ConvertirTuple("rc3")
