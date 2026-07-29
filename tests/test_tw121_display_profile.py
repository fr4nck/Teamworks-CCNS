#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "tw121_display_profile.py"
SPEC = importlib.util.spec_from_file_location("tw121_display_profile", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def read_config(path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    return parser


def test_normalize_theme_accepts_french_and_english_names():
    assert MODULE.normalize_theme("Système") == "Systeme"
    assert MODULE.normalize_theme("clair") == "Clair"
    assert MODULE.normalize_theme("DARK") == "Sombre"


def test_normalize_theme_rejects_unknown_value():
    try:
        MODULE.normalize_theme("violet")
    except ValueError as exc:
        assert "Thème invalide" in str(exc)
    else:
        raise AssertionError("Un thème inconnu doit être refusé")


def test_scale_bounds_are_inclusive():
    assert MODULE.normalize_scale(80) == 80
    assert MODULE.normalize_scale(200) == 200
    for value in (79, 201):
        try:
            MODULE.normalize_scale(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"L'échelle {value} doit être refusée")


def test_apply_profile_preserves_other_sections_and_creates_backup(tmp_path):
    path = tmp_path / "Customize.ini"
    path.write_text("[journal]\nactif = 1\n", encoding="utf-8")
    backup = MODULE.apply_profile(path, "Sombre", 150)
    assert backup is not None and backup.is_file()
    parser = read_config(path)
    assert parser.get("interface", "theme") == "Sombre"
    assert parser.getint("interface", "echelle_police") == 150
    assert parser.get("journal", "actif") == "1"
    assert MODULE.read_profile(path) == ("Sombre", 150)


def test_apply_profile_creates_missing_configuration(tmp_path):
    path = tmp_path / "nested" / "Customize.ini"
    backup = MODULE.apply_profile(path, "system", 100)
    assert backup is None
    MODULE.verify_profile(path, "Système", 100)


def test_verify_profile_detects_unexpected_persisted_value(tmp_path):
    path = tmp_path / "Customize.ini"
    path.write_text("[interface]\ntheme = Clair\nechelle_police = 125\n", encoding="utf-8")
    try:
        MODULE.verify_profile(path, "Sombre", 125)
    except ValueError as exc:
        assert "Persistance invalide" in str(exc)
    else:
        raise AssertionError("Une valeur persistée différente doit être signalée")


def test_read_profile_rejects_missing_interface_section(tmp_path):
    path = tmp_path / "Customize.ini"
    path.write_text("[journal]\nactif = 1\n", encoding="utf-8")
    try:
        MODULE.read_profile(path)
    except ValueError as exc:
        assert "Section [interface] absente" in str(exc)
    else:
        raise AssertionError("Une configuration sans section interface doit être refusée")


def test_sequential_backups_do_not_overwrite_each_other(tmp_path):
    path = tmp_path / "Customize.ini"
    path.write_text("[interface]\ntheme = Systeme\nechelle_police = 100\n", encoding="utf-8")
    first = MODULE.apply_profile(path, "Clair", 125)
    second = MODULE.apply_profile(path, "Sombre", 150)
    assert first is not None and second is not None
    assert first != second
    assert first.is_file() and second.is_file()


def test_restore_backup_recovers_original_profile_and_other_sections(tmp_path):
    path = tmp_path / "Customize.ini"
    path.write_text(
        "[interface]\ntheme = Systeme\nechelle_police = 100\n\n[journal]\nactif = 1\n",
        encoding="utf-8",
    )
    backup = MODULE.apply_profile(path, "Sombre", 175)
    assert backup is not None
    restored = MODULE.restore_backup(path, backup)
    assert restored == ("Systeme", 100)
    assert read_config(path).get("journal", "actif") == "1"


def test_restore_backup_rejects_missing_file(tmp_path):
    try:
        MODULE.restore_backup(tmp_path / "Customize.ini", tmp_path / "missing.bak")
    except ValueError as exc:
        assert "Sauvegarde introuvable" in str(exc)
    else:
        raise AssertionError("Une sauvegarde absente doit être refusée")
