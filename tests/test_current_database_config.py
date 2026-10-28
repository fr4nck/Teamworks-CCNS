"""Database selection is a pure, UI-neutral persistence operation."""

import json
from pathlib import Path

import pytest

from infrastructure.persistence.current_database_config import (
    read_current_database_name,
)


def test_selection_preserves_configured_local_and_network_names(tmp_path: Path) -> None:
    config = tmp_path / "Config.json"
    for name in ("ASSOCIATION", "Port;server;user;pass[RESEAU]DATA", "Test_\u00c9t\u00e9"):
        config.write_text(json.dumps({"nomFichier": name}), encoding="utf-8")
        assert read_current_database_name(config) == name


@pytest.mark.parametrize(
    "content",
    (
        "",
        "{invalid",
        "[]",
        "null",
        "123",
        "{}",
        '{"nomFichier": null}',
        '{"nomFichier": 42}',
        '{"nomFichier": false}',
    ),
)
def test_invalid_config_never_returns_non_string_name(tmp_path: Path, content: str) -> None:
    config = tmp_path / "Config.json"
    config.write_text(content, encoding="utf-8")
    assert read_current_database_name(config) == ""


def test_missing_or_non_utf8_config_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "Config.json"
    assert read_current_database_name(path) == ""
    path.write_bytes(b"\xff\xfe")
    assert read_current_database_name(path) == ""


def test_read_does_not_change_configuration(tmp_path: Path) -> None:
    config = tmp_path / "Config.json"
    payload = '{"nomFichier": "ASSO", "derniersFichiers": ["A"]}\n'
    config.write_text(payload, encoding="utf-8")
    assert read_current_database_name(config) == "ASSO"
    assert config.read_text(encoding="utf-8") == payload
