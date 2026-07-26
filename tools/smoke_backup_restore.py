#!/usr/bin/env python3
"""Exerce UTILS_Sauvegarde.Sauvegarde/Restauration sur des copies isolées."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
EXAMPLES = TEAMWORKS_DIR / "Static" / "Exemples"
FILES = ["Exemple_TDATA.dat", "Exemple_TDOCUMENTS.dat", "Exemple_TPHOTOS.dat"]
REPORT_DIR = ROOT / "artifacts" / "backup-restore-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"


class _ProgressDialog:
    def __init__(self, *args, **kwargs):
        self.updates = []

    def Update(self, *args, **kwargs):
        self.updates.append((args, kwargs))
        return True, False

    def Destroy(self):
        return None


class _MessageDialog:
    def __init__(self, *args, **kwargs):
        pass

    def ShowModal(self):
        import wx
        return wx.ID_YES

    def Destroy(self):
        return None


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _integrity(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        return str(connection.execute("PRAGMA integrity_check").fetchone()[0])


def run() -> None:
    sys.path.insert(0, str(TEAMWORKS_DIR))
    os.chdir(TEAMWORKS_DIR)

    import wx
    from Utils import UTILS_Fichiers
    from Utils import UTILS_Sauvegarde

    with tempfile.TemporaryDirectory(prefix="teamworks-backup-") as temp:
        root = Path(temp)
        source_dir = root / "source"
        restore_dir = root / "restore"
        temp_dir = root / "temp"
        backup_dir = root / "backup"
        for directory in (source_dir, restore_dir, temp_dir, backup_dir):
            directory.mkdir(parents=True)

        for filename in FILES:
            shutil.copy2(EXAMPLES / filename, source_dir / filename)

        original_hashes = {name: _digest(source_dir / name) for name in FILES}
        current_data_dir = source_dir

        def get_rep_data(fichier=None):
            if fichier in (None, ""):
                return str(current_data_dir)
            return str(current_data_dir / fichier)

        def get_rep_temp(fichier=None):
            if fichier in (None, ""):
                return str(temp_dir)
            return str(temp_dir / fichier)

        UTILS_Fichiers.GetRepData = get_rep_data
        UTILS_Fichiers.GetRepTemp = get_rep_temp
        wx.ProgressDialog = _ProgressDialog
        wx.MessageDialog = _MessageDialog

        print("TEAMWORKS_BACKUP_STAGE:create", flush=True)
        saved = UTILS_Sauvegarde.Sauvegarde(
            listeFichiersLocaux=FILES,
            nom="recette_teamworks",
            repertoire=str(backup_dir),
        )
        archive = backup_dir / "recette_teamworks.twd"
        assert saved is True
        assert archive.is_file()
        assert UTILS_Sauvegarde.VerificationZip(str(archive)) is True
        assert sorted(UTILS_Sauvegarde.GetListeFichiersZIP(str(archive))) == sorted(FILES)

        print("TEAMWORKS_BACKUP_STAGE:restore", flush=True)
        current_data_dir = restore_dir
        restored = UTILS_Sauvegarde.Restauration(
            fichier=str(archive),
            listeFichiersLocaux=FILES,
        )
        assert sorted(restored) == sorted(name[:-4] for name in FILES)

        print("TEAMWORKS_BACKUP_STAGE:verify", flush=True)
        restored_hashes = {name: _digest(restore_dir / name) for name in FILES}
        assert restored_hashes == original_hashes
        assert {_integrity(restore_dir / name) for name in FILES} == {"ok"}

        print("TEAMWORKS_BACKUP_RESTORE_OK", flush=True)
        print(f"archive={archive}", flush=True)
        print(f"files={','.join(FILES)}", flush=True)


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        run()
        REPORT.write_text("TEAMWORKS_BACKUP_RESTORE_OK\n", encoding="utf-8")
        return 0
    except Exception:
        diagnostic = traceback.format_exc()
        REPORT.write_text(diagnostic, encoding="utf-8")
        print(diagnostic, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
