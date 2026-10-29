"""La base active est toujours nommée ; sans base sélectionnée, rien n'est ouvert."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

import launcher  # noqa: E402


def test_local_base_label_names_the_exact_file():
    db = SimpleNamespace(isNetwork=False, nomFichier=r"C:\Teamworks\Portable\Data\Recette_TDATA.dat")
    assert launcher.describe_active_database(db) == (
        r"Base locale SQLite C:\Teamworks\Portable\Data\Recette_TDATA.dat"
    )


def test_network_label_names_server_and_base_but_never_the_password_token():
    db = SimpleNamespace(isNetwork=True, nomFichier="3306;srv-rh;teamworks;SECRET-TOKEN[RESEAU]Structure_TDATA")
    label = launcher.describe_active_database(db)
    assert "structure_tdata" in label and "srv-rh:3306" in label and "teamworks" in label
    assert "SECRET" not in label


def _fake_environment(monkeypatch, tmp_path, config):
    config_path = tmp_path / "Config.json"
    if config is not None:
        config_path.write_text(json.dumps(config), encoding="utf-8")
    opened = []

    def forbidden_db(*args, **kwargs):
        opened.append(args)
        raise AssertionError("aucune base ne doit être ouverte")

    monkeypatch.setattr(launcher, "import_chemins_safely", lambda: None)
    monkeypatch.setitem(sys.modules, "GestionDB", SimpleNamespace(DB=forbidden_db))
    monkeypatch.setitem(
        sys.modules,
        "Utils",
        SimpleNamespace(UTILS_Fichiers=SimpleNamespace(GetRepUtilisateur=lambda name: str(tmp_path / name))),
    )
    return opened


@pytest.mark.parametrize("config", [None, {}, {"nomFichier": ""}])
def test_no_selected_base_is_refused_before_any_opening(monkeypatch, tmp_path, config):
    opened = _fake_environment(monkeypatch, tmp_path, config)
    report, refusal = launcher.precheck_production_database()
    assert report is None
    assert "Aucune base Teamworks n'est sélectionnée" in refusal
    assert str(tmp_path / "Config.json") in refusal
    assert opened == []
