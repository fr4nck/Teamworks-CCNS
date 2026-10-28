"""Regression tests for the historical MySQL reference format."""

import ast
from pathlib import Path

import pytest

from infrastructure.persistence.legacy_network_target import (
    LegacyNetworkTarget,
    parse_legacy_network_target,
)


def test_network_target_preserves_legacy_aliases_and_database_casing():
    ref = "3307;server;operator;#64#c2VjcmV0[RESEAU]Equipe_TDATA"
    result = parse_legacy_network_target(ref)
    assert result == LegacyNetworkTarget(3307, "server", "operator", "#64#c2VjcmV0", "equipe_tdata")
    assert result.as_legacy_parameters() == {
        "port": 3307,
        "hote": "server",
        "host": "server",
        "user": "operator",
        "utilisateur": "operator",
        "mdp": "#64#c2VjcmV0",
        "password": "#64#c2VjcmV0",
        "fichier": "equipe_tdata",
    }


def test_legacy_target_preserves_empty_fields_suffix_and_repeated_marker():
    target = parse_legacy_network_target("03306;;;[RESEAU]R\u00c9SEAU[RESEAU]_TDATA")
    assert (target.port, target.host, target.user, target.password_token) == (3306, "", "", "")
    assert target.database == "r\u00e9seau_tdata"


@pytest.mark.parametrize(
    "reference",
    ["", "3306;server;user;secret", "3306;server;user[RESEAU]data",
     "3306;server;user;secret;extra[RESEAU]data", "bogus;server;user;secret[RESEAU]db"],
)
def test_malformed_network_target_never_echoes_secrets(reference):
    with pytest.raises((ValueError, TypeError)) as exc:
        parse_legacy_network_target(reference)
    assert "secret" not in str(exc.value)
    assert "server" not in str(exc.value)


def test_non_string_target_fails_without_data_leak():
    with pytest.raises(TypeError, match="must be a string"):
        parse_legacy_network_target(None)


def test_password_is_redacted_from_object_repr():
    target = parse_legacy_network_target("3306;db;user;confidential[RESEAU]RH")
    assert "confidential" not in repr(target)
    assert "password_token" not in repr(target)


def test_network_target_module_has_no_ui_or_legacy_imports():
    path = Path(__file__).resolve().parents[1] / "infrastructure/persistence/legacy_network_target.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    assert not any(name.split(".")[0] in {"wx", "PySide6", "teamworks", "GestionDB"} for name in names)
