from pathlib import Path
import re
import shutil
import datetime

root = Path.cwd()
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

def backup(path: Path):
    if path.exists():
        shutil.copy2(path, path.with_suffix(path.suffix + f".bak-{stamp}"))

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")

def write(path: Path, content: str):
    path.write_text(content, encoding="utf-8", newline="\n")

# 1) Corrige GestionDB.py : isNetwork utilisé avant initialisation
p = root / "teamworks" / "GestionDB.py"
backup(p)
txt = read(p)

pattern = r'class DB:\s*\n    def __init__\(self, suffixe="DATA", nomFichier="", modeCreation=False, IDconnexion=None\):.*?(?=\n    def GetNomPosteReseau\(self\):)'
replacement = '''class DB:
    def __init__(self, suffixe="DATA", nomFichier="", modeCreation=False, IDconnexion=None):
        """ Utiliser GestionDB.DB(suffixe="PHOTOS") pour accéder à un fichier utilisateur """
        """ Utiliser GestionDB.DB(nomFichier=Chemins.GetStaticPath("Databases/Geographie.dat"), suffixe=None) pour ouvrir un autre type de fichier """
        self.nomFichier = nomFichier
        self.modeCreation = modeCreation

        # Mémorisation de l'ouverture de la connexion et des requêtes
        if IDconnexion == None:
            self.IDconnexion = random.randint(0, 1000000)
        else:
            self.IDconnexion = IDconnexion
        DICT_CONNEXIONS[self.IDconnexion] = []

        # On ajoute le préfixe de type de fichier et l'extension du fichier
        if MODE_TEAMWORKS == True and suffixe not in ("", None):
            if suffixe[0] != "T":
                suffixe = _(u"T%s") % suffixe

        if suffixe != None:
            self.nomFichier += u"_%s" % suffixe

        # Est-ce une connexion réseau ?
        if "[RESEAU]" in self.nomFichier:
            self.isNetwork = True
        else:
            self.isNetwork = False
            if suffixe != None:
                self.nomFichier = UTILS_Fichiers.GetRepData(u"%s.dat" % self.nomFichier)

        # Ouverture de la base de données
        with DiagnosticPerformance.mesurer("connexion", "GestionDB.DB.__init__", {"reseau": self.isNetwork}):
            if self.isNetwork == True:
                self.OuvertureFichierReseau(self.nomFichier, suffixe)
            else:
                self.OuvertureFichierLocal(self.nomFichier)

'''
txt2, n = re.subn(pattern, replacement, txt, flags=re.S)
if n != 1:
    raise RuntimeError("GestionDB.py : bloc DB.__init__ non trouvé ou ambigu")
write(p, txt2)

# 2) Corrige CTRL_Bouton_image.py : indentation PIL / resize
p = root / "teamworks" / "Ctrl" / "CTRL_Bouton_image.py"
backup(p)
txt = read(p)

txt = re.sub(
    r'(\n\s*self\.margesTexte = margesTexte\s*\n)(?:\s*resample_filter = Image\.Resampling\.LANCZOS\s*\n\s*except AttributeError:\s*\n\s*resample_filter = getattr\(Image, "LANCZOS", Image\.BICUBIC\)\s*\n\s*img = img\.resize\(self\.tailleImage, resample_filter\)\s*\n)?\s*self\.MAJ\(\)\s*',
    r'\1        self.MAJ()\n',
    txt,
    flags=re.S,
)

maj_pattern = r'    def MAJ\(self\):.*?(?=\n    def SetImage\(self, cheminImage=""\):)'
maj_replacement = '''    def MAJ(self):
        # Redimensionne et ajoute des marges autour de l'image
        if self.cheminImage not in ("", None):
            img = Image.open(self.cheminImage)

            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                resample_filter = getattr(Image, "LANCZOS", Image.BICUBIC)

            img = img.resize(self.tailleImage, resample_filter)
            img = ImageOps.expand(img, border=self.margesImage)
            img = PILtoWx(img)
            bmp = img.ConvertToBitmap()
        else:
            bmp = wx.NullBitmap

        # MAJ du bouton
        self.SetBitmap(bmp, self.positionImage)
        if self.cheminImage not in ("", None):
            self.SetBitmapMargins(self.margesTexte)
        self.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetInitialSize()

'''
txt2, n = re.subn(maj_pattern, maj_replacement, txt, flags=re.S)
if n != 1:
    raise RuntimeError("CTRL_Bouton_image.py : bloc MAJ non trouvé ou ambigu")
write(p, txt2)

# 3) Corrige CTRL_ObjectListView.py : wxPython 4 refuse les float dans SetSize / SetDimensions
p = root / "teamworks" / "Ctrl" / "CTRL_ObjectListView.py"
backup(p)
txt = read(p)

txt = txt.replace(
    "self.stEmptyListMsg.SetSize(0, sz.GetHeight()/proportion, sz.GetWidth(), sz.GetHeight())",
    "self.stEmptyListMsg.SetSize(0, int(sz.GetHeight()/proportion), int(sz.GetWidth()), int(sz.GetHeight()))",
)
txt = txt.replace(
    "self.stEmptyListMsg.SetDimensions(0, sz.GetHeight() / proportion, sz.GetWidth(), sz.GetHeight())",
    "self.stEmptyListMsg.SetDimensions(0, int(sz.GetHeight() / proportion), int(sz.GetWidth()), int(sz.GetHeight()))",
)
txt = txt.replace(
    "self.stEmptyListMsg.SetSize(0, sz.GetHeight() / proportion, sz.GetWidth(), sz.GetHeight())",
    "self.stEmptyListMsg.SetSize(0, int(sz.GetHeight() / proportion), int(sz.GetWidth()), int(sz.GetHeight()))",
)
write(p, txt)

# 4) Ajoute compat htmlentitydefs pour vieux code Python 2
p = root / "teamworks" / "htmlentitydefs.py"
backup(p)
write(p, '''# -*- coding: utf-8 -*-
"""
Compatibilité Python 2 pour UTIL_Html2text sous Python 3.
"""

import importlib.util
import pathlib
import sysconfig

_entities_path = pathlib.Path(sysconfig.get_paths()["stdlib"]) / "html" / "entities.py"
_spec = importlib.util.spec_from_file_location("_stdlib_html_entities", _entities_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

name2codepoint = _mod.name2codepoint
codepoint2name = _mod.codepoint2name
entitydefs = _mod.entitydefs
html5 = _mod.html5
''')

# 5) Ajoute lanceur portable Windows
p = root / "Lancer-Teamworks-CCNS.bat"
backup(p)
p.write_text('''@echo off
cd /d "%~dp0"
set PYTHONPATH=%CD%;%CD%\\teamworks
py -3.11 teamworks\\Teamworks.py
pause
''', encoding="ascii", newline="\r\n")

print("Correctifs appliqués.")
print("Backups créés avec suffixe .bak-" + stamp)
