#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gardes statiques du lanceur PowerShell TW-122."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "tools" / "tw121_display_profile.ps1"


def _source() -> str:
    assert LAUNCHER.is_file(), "Le lanceur PowerShell TW-122 doit être livré"
    return LAUNCHER.read_text(encoding="utf-8")


def test_launcher_requires_explicit_configuration_path():
    source = _source()
    assert "[Parameter(Mandatory = $true)]" in source
    assert "[string]$Config" in source


def test_launcher_limits_theme_and_font_scale_values():
    source = _source()
    assert '[ValidateSet("Systeme", "Système", "Clair", "Sombre")]' in source
    assert "[ValidateRange(80, 200)]" in source


def test_launcher_supports_non_destructive_persistence_check():
    source = _source()
    assert "[switch]$CheckOnly" in source
    assert '$Arguments += "--check-only"' in source
    assert "Configuration vérifiée sans modification." in source


def test_launcher_supports_explicit_restore_mode():
    source = _source()
    assert "[string]$Restore" in source
    assert '$Arguments += @("--restore", $Restore)' in source
    assert "Configuration restaurée. Relancez Teamworks-CCNS." in source


def test_launcher_propagates_python_failure_exit_code():
    source = _source()
    assert "$ExitCode = $LASTEXITCODE" in source
    assert "exit $ExitCode" in source
