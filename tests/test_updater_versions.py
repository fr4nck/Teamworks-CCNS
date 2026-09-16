from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"
VERSION_UTILS = ROOT / "teamworks" / "Utils" / "UTILS_Versions.py"
UPDATER = ROOT / "teamworks" / "Dlg" / "DLG_Updater.py"


def _load_version_utils():
    spec = spec_from_file_location("teamworks_version_utils", VERSION_UTILS)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERSIONS = _load_version_utils()


@pytest.mark.parametrize(
    "value",
    ["0.9.2", "0.9.2-rc1", "0.9.2-rc2", "0.9.2-rc3"],
)
def test_parse_supported_versions(value):
    parsed = VERSIONS.parse_version(value)
    assert isinstance(parsed, tuple)


def test_release_candidate_ordering_precedes_final_release():
    assert VERSIONS.parse_version("0.9.2-rc1") < VERSIONS.parse_version("0.9.2-rc2")
    assert VERSIONS.parse_version("0.9.2-rc2") < VERSIONS.parse_version("0.9.2-rc3")
    assert VERSIONS.parse_version("0.9.2-rc3") < VERSIONS.parse_version("0.9.2")


@pytest.mark.parametrize(
    "value",
    ["", "0.9", "0.9.2-beta1", "0.9.2-rc0", "garbage"],
)
def test_invalid_versions_are_rejected_explicitly(value):
    with pytest.raises(ValueError):
        VERSIONS.parse_version(value)


def test_canonical_version_file_uses_supported_syntax():
    current = VERSIONS.read_version_file(VERSION_FILE)
    assert VERSIONS.parse_version(current)


def test_ui_safe_reader_does_not_raise_for_missing_or_invalid_version(tmp_path):
    invalid = tmp_path / "VERSION"
    invalid.write_text("0.9.2-beta1\n", encoding="utf-8")

    assert VERSIONS.read_first_valid_version([tmp_path / "missing", invalid]) is None


def test_disabled_updater_contains_no_historical_teamworks_endpoints():
    source = UPDATER.read_text(encoding="utf-8")

    compile(source, str(UPDATER), "exec")
    assert "teamworks.ovh" not in source
    assert "Noethys/Teamworks" not in source
    assert "urlopen(" not in source
    assert "urlretrieve(" not in source
    assert "La mise à jour automatique n’est pas encore disponible pour Teamworks-CCNS." in source
