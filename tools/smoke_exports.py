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
    destinations: list[Path] = []

    def __init__(self, *args, **kwargs):
        if not self.destinations:
            raise RuntimeError("aucune destination d'export préparée")
        self.path = self.destinations.pop(0)

    def SetFilterIndex(self, index):
        self.filter_index = index

    def ShowModal(self):
        import wx
        return wx.ID_OK

    def GetPath(self):
        return str(self.path)

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


class _ChoiceDialog:
    def __init__(self, *args, **kwargs):
        pass

    def ShowModal(self):
        return 100

    def Destroy(self):
        return None


def main() -> int:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(TEAMWORKS_DIR))
    os.chdir(TEAMWORKS_DIR)

    import wx
    from Utils import UTILS_Export

    app = wx.App(False)
    try:
        with tempfile.TemporaryDirectory(prefix="teamworks-exports-") as temp:
            directory = Path(temp)
            text_path = directory / "recette_accents.txt"
            excel_path = directory / "recette_tableau.xlsx"
            _FileDialog.destinations = [text_path, excel_path]

            wx.FileDialog = _FileDialog
            wx.MessageDialog = _MessageDialog
            UTILS_Export.DLG_Choix_action = _ChoiceDialog
            UTILS_Export.FonctionsPerso.LanceFichierExterne = lambda path: None

            columns = [
                ("Prénom", None, 18, "prenom"),
                ("Commune", None, 24, "commune"),
                ("Durée", None, 10, "duree"),
            ]
            rows = [
                ["Élodie", "L'Haÿ-les-Roses", "01:30"],
                ["Andréa", "La Guerche-de-Bretagne", "02:15"],
            ]

            UTILS_Export.ExportTexte(
                listeColonnes=columns,
                listeValeurs=rows,
                autoriseSelections=False,
            )
            assert text_path.is_file()
            text = text_path.read_text(encoding="utf-8")
            expected = (
                "Prénom;Commune;Durée\n"
                "Élodie;L'Haÿ-les-Roses;01:30\n"
                "Andréa;La Guerche-de-Bretagne;02:15"
            )
            assert text == expected
            assert text_path.read_bytes().decode("utf-8") == expected

            UTILS_Export.ExportExcel(
                titre="Recette",
                listeColonnes=columns,
                listeValeurs=rows,
                autoriseSelections=False,
            )
            assert excel_path.is_file()
            assert excel_path.stat().st_size > 0

            with zipfile.ZipFile(excel_path) as workbook:
                assert workbook.testzip() is None
                names = set(workbook.namelist())
                assert "xl/workbook.xml" in names
                assert "xl/worksheets/sheet1.xml" in names
                shared = workbook.read("xl/sharedStrings.xml").decode("utf-8")
                for value in (
                    "Prénom",
                    "Commune",
                    "Durée",
                    "Élodie",
                    "L'Haÿ-les-Roses",
                    "Andréa",
                    "La Guerche-de-Bretagne",
                ):
                    assert value in shared

            print("TEAMWORKS_EXPORTS_OK")
            print(f"text={text_path.name}:{text_path.stat().st_size}")
            print(f"excel={excel_path.name}:{excel_path.stat().st_size}")
    finally:
        app.Destroy()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
