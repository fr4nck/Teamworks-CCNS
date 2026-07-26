#!/usr/bin/env python3
"""Exerce les exports texte et Excel réels sans interaction utilisateur."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"


class _FileDialog:
    paths: list[str] = []

    def __init__(self, *args, **kwargs):
        if not self.paths:
            raise RuntimeError("aucun chemin d'export préparé")
        self.path = self.paths.pop(0)

    def SetFilterIndex(self, index):
        return None

    def ShowModal(self):
        import wx
        return wx.ID_OK

    def GetPath(self):
        return self.path

    def Destroy(self):
        return None


class _MessageDialog:
    def __init__(self, *args, **kwargs):
        pass

    def ShowModal(self):
        import wx
        return wx.ID_NO

    def Destroy(self):
        return None


class _SaveChoiceDialog:
    def __init__(self, *args, **kwargs):
        pass

    def ShowModal(self):
        return 100

    def Destroy(self):
        return None


def main() -> int:
    sys.path.insert(0, str(TEAMWORKS_DIR))
    os.chdir(TEAMWORKS_DIR)

    import wx
    from Utils import UTILS_Export

    columns = [
        ("Nom", "left", 120, "nom"),
        ("Prénom", "left", 100, "prenom"),
        ("Montant", "right", 80, "montant"),
    ]
    values = [
        ["DUPONT", "Élodie", "12,50"],
        ["MARTIN", "Noël", "25,00"],
    ]

    with tempfile.TemporaryDirectory(prefix="teamworks-exports-") as temp:
        output = Path(temp)
        text_path = output / "personnes.txt"
        excel_path = output / "personnes.xlsx"

        _FileDialog.paths = [str(text_path), str(excel_path)]
        wx.FileDialog = _FileDialog
        wx.MessageDialog = _MessageDialog
        UTILS_Export.DLG_Choix_action = _SaveChoiceDialog

        UTILS_Export.ExportTexte(
            titre="Personnes",
            listeColonnes=columns,
            listeValeurs=values,
            autoriseSelections=False,
        )
        assert text_path.is_file()
        text = text_path.read_text(encoding="utf-8")
        assert "Nom;Prénom;Montant" in text
        assert "DUPONT;Élodie;12,50" in text
        assert "MARTIN;Noël;25,00" in text

        UTILS_Export.ExportExcel(
            titre="Personnes",
            listeColonnes=columns,
            listeValeurs=values,
            autoriseSelections=False,
        )
        assert excel_path.is_file()
        assert zipfile.is_zipfile(excel_path)
        with zipfile.ZipFile(excel_path) as archive:
            names = set(archive.namelist())
            assert "xl/workbook.xml" in names
            assert "xl/worksheets/sheet1.xml" in names
            shared = archive.read("xl/sharedStrings.xml").decode("utf-8")
            assert "Élodie" in shared
            assert "Noël" in shared

        print("TEAMWORKS_FILE_EXPORTS_OK")
        print(f"text={text_path.stat().st_size}")
        print(f"xlsx={excel_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
