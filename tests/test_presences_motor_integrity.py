import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'teamworks' / 'Dlg' / 'DLG_Saisie_presence.py'
SOURCE = PATH.read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)


def _method(name):
    node = next(n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(SOURCE, node)


def test_presence_rejects_24h00_for_start_and_end():
    source = _method('ValidationDonnees')
    assert 'heure_debut >= "24:00"' in source
    assert 'heure_fin >= "24:00"' in source
    assert 'heure_debut > "24:00"' not in source
    assert 'heure_fin > "24:00"' not in source


def test_live_time_validation_never_accepts_hour_24():
    source = _method('_valider_heure_pendant_saisie')
    assert '0 <= int(texte_brut[:2]) <= 23' in source
    assert '<= 24' not in source


def test_bulk_presence_save_is_one_transaction():
    source = _method('SauvegardeNouveau')
    assert 'commit=False' in source
    assert source.count('DB.Commit()') == 1
    assert 'DB.connexion.rollback()' in source
    assert 'finally:' in source
    assert source.count('DB.Close()') == 1
    assert source.rindex('DB.ReqInsert(') < source.index('DB.Commit()')
    assert source.index('DB.Commit()') < source.index('DB.Close()')


def test_overlap_remains_a_business_skip_not_a_transaction_failure():
    source = _method('SauvegardeNouveau')
    assert 'liste_exceptions.append' in source
    assert 'continue' in source
    assert source.index('liste_exceptions.append') < source.index('DB.ReqInsert(')
