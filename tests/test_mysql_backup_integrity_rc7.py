# -*- coding: utf-8 -*-
"""Anti-sauvegardes-partielles : tests sans base de donnees ni fichier prive."""
import ast
import importlib.util
from pathlib import Path
import os
import sys


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "teamworks/Utils/UTILS_MySQL_backup.py"
BACKUP = ROOT / "teamworks/Utils/UTILS_Sauvegarde.py"


def _helper():
    spec = importlib.util.spec_from_file_location("backup_mysql_isolated", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hidden_console_on_windows_and_unix():
    helper = _helper()
    assert helper._creationflags(platform="nt") != 0
    assert helper._creationflags(platform="posix") == 0


def test_successful_export_waits_for_child_and_writes_full_output(tmp_path):
    helper = _helper()
    output = tmp_path / "sample.sql"
    result = helper.ExporterSQL(
        [sys.executable, "-c", "import sys; sys.stdout.write('DATA:abc\\n')"],
        str(output),
    )
    assert result["erreur"] is None
    assert result["code_retour"] == 0
    assert output.read_text() == "DATA:abc\n"
    assert result["octets"] == len(output.read_bytes())


def test_failure_cannot_be_reported_as_success_and_does_not_leak_secrets(tmp_path):
    helper = _helper()
    output = tmp_path / "failed.sql"
    result = helper.ExporterSQL(
        [sys.executable, "-c",
         "import sys; sys.stderr.write('fail secret-value'); sys.exit(7)"],
        str(output),
        secrets=("secret-value",),
    )
    assert result["code_retour"] == 7
    assert result["erreur"]
    assert "secret-value" not in result["erreur"]
    assert "[masqué]" in result["erreur"]


def test_empty_export_is_not_a_valid_backup(tmp_path):
    helper = _helper()
    output = tmp_path / "empty.sql"
    result = helper.ExporterSQL(
        [sys.executable, "-c", "pass"],
        str(output),
    )
    assert result["code_retour"] == 0
    assert result["octets"] == 0
    assert result["erreur"]


def test_stalled_child_is_stopped_not_waited_on_forever(tmp_path):
    helper = _helper()
    output = tmp_path / "blocked.sql"
    result = helper.ExporterSQL(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        str(output), inactivite=0.1, duree_max=3,
    )
    assert result["erreur"]
    assert "progression" in result["erreur"] or "durée" in result["erreur"]


def test_backup_refuses_missing_network_connection_before_zip_is_created():
    source = BACKUP.read_text(encoding="utf-8")
    assert "if listeFichiersReseau and dictConnexion is None:" in source
    before_zip = source.index("if listeFichiersReseau and dictConnexion is None:")
    zip_create = source.index("fichierZip = zipfile.ZipFile(")
    assert before_zip < zip_create
    assert "if listeFichiersReseau and dictConnexion != None :" not in source


def test_archive_is_validated_and_published_atomically():
    source = BACKUP.read_text(encoding="utf-8")
    assert "UTILS_MySQL_backup.ExporterSQL(" in source
    assert "archive_controle.testzip()" in source
    assert "attendus.difference(membres)" in source
    assert "os.replace(copie_temp, fichierDest)" in source
    assert "tempfile.mkstemp(" in source
    assert "shutil.copy2(fichier_source, fichierDest)" not in source
    assert "--skip-lock-tables" in source
    assert "--single-transaction" in source
    assert "--routines" in source
    assert "--events" in source
    assert "--triggers" in source
