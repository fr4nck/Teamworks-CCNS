#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from tools import diagnostic_installation


def test_build_report_success(tmp_path: Path) -> None:
    root = tmp_path / "package"
    for relative_path in diagnostic_installation.REQUIRED_RESOURCES:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test")

    user_directory = tmp_path / "user"
    report, success = diagnostic_installation.build_report(root, user_directory)

    assert success is True
    assert "Résultat global: OK" in report
    assert str(user_directory) in report


def test_build_report_reports_missing_resources(tmp_path: Path) -> None:
    root = tmp_path / "empty-package"
    root.mkdir()

    report, success = diagnostic_installation.build_report(root, tmp_path / "user")

    assert success is False
    assert "[ERREUR] Ressource" in report
    assert "Résultat global: ERREUR" in report
