"""Garde-fous sans serveur ni wx natif pour l'export XLSX Linux."""

import ast
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def _charger_fonction(relatif, nom):
    chemin = ROOT / relatif
    arbre = ast.parse(chemin.read_text(encoding="utf-8"), filename=str(chemin))
    fonction = next(
        n for n in arbre.body if isinstance(n, ast.FunctionDef) and n.name == nom
    )
    module = ast.Module(body=[fonction], type_ignores=[])
    return compile(module, str(chemin), "exec")


def test_export_xlsx_lignes_sans_identifiant_visible(tmp_path):
    """Une civilité/nom en première colonne n'est pas un identifiant."""
    suivi = {}
    destination = tmp_path / "Export Excel avec espaces.xlsx"

    class DialogueSelection:
        def __init__(self, *args, **kwargs):
            suivi["ids"] = kwargs["listeIDs"]

        def ShowModal(self):
            return 1

        def GetSelections(self):
            return [1]

        def Destroy(self):
            pass

    class DialogueFichier:
        def __init__(self, *args, **kwargs):
            pass

        def SetFilterIndex(self, index):
            pass

        def ShowModal(self):
            return 1

        def GetPath(self):
            return str(destination)

        def Destroy(self):
            pass

    class DialogueConfirmation:
        def __init__(self, *args, **kwargs):
            pass

        def ShowModal(self):
            return 2

        def Destroy(self):
            pass

    class Feuille:
        def __init__(self):
            self.cellules = []

        def write(self, ligne, colonne, valeur):
            self.cellules.append((ligne, colonne, valeur))

        def set_column(self, *args):
            pass

    class Classeur:
        def __init__(self, chemin, options):
            suivi["chemin"] = chemin
            suivi["options"] = options
            self.feuille = Feuille()
            suivi["feuille"] = self.feuille

        def add_worksheet(self):
            return self.feuille

        def close(self):
            suivi["ferme"] = True

    wx_factice = SimpleNamespace(
        ID_OK=1, ID_NO=2, FD_SAVE=4, YES_NO=8, NO_DEFAULT=16,
        ICON_EXCLAMATION=32, ICON_QUESTION=64,
        StandardPaths=SimpleNamespace(
            Get=lambda: SimpleNamespace(GetDocumentsDir=lambda: str(tmp_path))
        ),
        FileDialog=DialogueFichier,
        MessageDialog=DialogueConfirmation,
    )
    contexte = {
        "wx": wx_factice,
        "_": lambda texte: texte,
        "os": os,
        "xlsxwriter": SimpleNamespace(Workbook=Classeur),
        "DLG_Selection_liste": SimpleNamespace(Dialog=DialogueSelection),
        "FonctionsPerso": SimpleNamespace(LanceFichierExterne=lambda _: None),
    }
    exec(
        _charger_fonction("teamworks/Utils/UTILS_Excel.py", "Excel"),
        contexte,
    )
    contexte["Excel"](
        None,
        [("Civilité", "left", 100, "civilite"), ("Nom", "left", 120, "nom")],
        [["Mme", "=1+1"], ["M.", "Nom choisi"]],
    )

    assert suivi["ids"] == [0, 1]
    assert suivi["ferme"] is True
    assert suivi["chemin"] == str(destination)
    assert suivi["options"]["strings_to_formulas"] is False
    assert suivi["options"]["strings_to_urls"] is False
    assert suivi["feuille"].cellules == [
        (0, 0, "Civilité"), (0, 1, "Nom"),
        (1, 0, "M."), (1, 1, "Nom choisi"),
    ]


def test_les_sept_blocages_linux_sont_supprimes():
    interfaces = [
        "teamworks/Ctrl/CTRL_Personnes.py",
        "teamworks/Ctrl/CTRL_Recrutement.py",
    ]
    for chemin in interfaces:
        source = (ROOT / chemin).read_text(encoding="utf-8")
        assert "self.bouton_export_excel.Enable(False)" not in source

    coeurs = [
        "OL_personnes_core.py",
        "OL_candidats_core.py",
        "OL_candidatures_core.py",
        "OL_entretiens_core.py",
        "OL_emplois_core.py",
    ]
    for fichier in coeurs:
        chemin = ROOT / "teamworks/Ol" / fichier
        arbre = ast.parse(chemin.read_text(encoding="utf-8"))
        methodes = [
            methode
            for classe in arbre.body if isinstance(classe, ast.ClassDef)
            for methode in classe.body if isinstance(methode, ast.FunctionDef)
            and methode.name == "ExportExcel"
        ]
        assert len(methodes) == 1, fichier
        export = ast.get_source_segment(chemin.read_text(encoding="utf-8"), methodes[0])
        assert "sys.platform" not in export, fichier
        assert "UTILS_Excel.Excel(" in export, fichier


def test_ouverture_fichier_linux_sans_shell(monkeypatch):
    appels = []
    def lancement(arguments, **options):
        appels.append((arguments, options))
        return object()

    monkeypatch.setattr(subprocess, "Popen", lancement)
    contexte = {"sys": SimpleNamespace(platform="linux"), "os": os}
    exec(
        _charger_fonction("teamworks/FonctionsPerso.py", "LanceFichierExterne"),
        contexte,
    )
    chemin = "/tmp/Export Excel; harmless.xlsx"
    contexte["LanceFichierExterne"](chemin)

    assert appels == [(
        ["xdg-open", chemin],
        {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        },
    )]
