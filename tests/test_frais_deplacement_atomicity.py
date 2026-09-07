from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'teamworks' / 'Dlg' / 'DLG_Saisie_deplacement.py'
SOURCE = PATH.read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)

def _method(name):
    for node in ast.walk(TREE):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(SOURCE, node)
    raise AssertionError(name)

def test_ok_saves_deplacement_and_distance_in_one_transaction():
    source = _method('OnBoutonOk')
    assert 'DB = GestionDB.DB()' in source
    assert 'self.SauvegardeDeplacement(DB=DB, commit=False)' in source
    assert 'self.SauvegardeDistance(DB=DB, commit=False)' in source
    assert source.count('DB.Commit()') == 1
    assert 'DB.connexion.rollback()' in source
    assert 'finally:' in source and 'DB.Close()' in source

def test_deplacement_write_can_join_external_transaction():
    source = _method('SauvegardeDeplacement')
    assert 'def SauvegardeDeplacement(self, DB=None, commit=True)' in source
    assert 'commit=commit' in source
    assert 'DB.Commit()' not in source

def test_distance_cache_write_can_join_external_transaction():
    source = _method('SauvegardeDistance')
    assert 'def SauvegardeDistance(self, DB=None, commit=True)' in source
    assert source.count('commit=commit') == 2
    assert 'DB.Commit()' not in source
