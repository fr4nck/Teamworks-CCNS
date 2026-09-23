# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    'teamworks/Dlg/DLG_Parametres_horloge.py',
    'teamworks/Dlg/DLG_Parametres_dossiers.py',
    'teamworks/Dlg/DLG_Parametres_calendrier.py',
)

def _on_left_link(path):
    text = (ROOT / path).read_text(encoding='utf-8')
    tree = ast.parse(text)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Dialog')
    func = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'OnLeftLink')
    lines = text.splitlines()
    return '\n'.join(lines[func.lineno - 1:func.end_lineno])

def test_three_parameter_screens_use_supported_defaults_database_api():
    for path in FILES:
        body = _on_left_link(path)
        assert 'nomDB="Defaut.db3"' not in body
        assert 'nomFichier=Chemins.GetStaticPath("Databases/Defaut.dat")' in body
        assert 'suffixe=None' in body

def test_three_parameter_screens_keep_same_constructor_shape():
    marker = 'DB = GestionDB.DB(\n            nomFichier=Chemins.GetStaticPath("Databases/Defaut.dat"),\n            suffixe=None,\n        )'
    for path in FILES:
        assert marker in _on_left_link(path)
