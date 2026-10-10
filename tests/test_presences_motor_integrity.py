import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'teamworks' / 'Dlg' / 'DLG_Saisie_presence.py'
SOURCE = PATH.read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)
AMPLITUDE_PATH = ROOT / 'teamworks' / 'Dlg' / 'DLG_Saisie_heures.py'
AMPLITUDE_SOURCE = AMPLITUDE_PATH.read_text(encoding='utf-8')


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


def test_planning_amplitude_never_accepts_hour_24_before_datetime_time():
    assert '0<= int(texteBrut[:2]) <=24' not in AMPLITUDE_SOURCE
    assert AMPLITUDE_SOURCE.count('0<= int(texteBrut[:2]) <=23') == 2
    assert 'heureDebut >= "24:00"' in AMPLITUDE_SOURCE
    assert 'heureFin >= "24:00"' in AMPLITUDE_SOURCE
    assert 'datetime.time(int(heureTuple[0]), int(heureTuple[1]))' in AMPLITUDE_SOURCE


def test_all_presence_clock_inputs_share_the_23h59_ceiling():
    assert ' <=24' not in SOURCE
    assert ' > "24:00"' not in SOURCE
    assert ' <=24' not in AMPLITUDE_SOURCE
    assert ' > "24:00"' not in AMPLITUDE_SOURCE


import sqlite3
from contextlib import closing
from types import SimpleNamespace
import pytest


@pytest.mark.parametrize("failure", [False, True])
def test_bulk_save_commits_all_rows_or_rolls_back_everything(tmp_path, failure):
    database = tmp_path / "presences.sqlite"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE presences (IDpresence INTEGER PRIMARY KEY, IDpersonne INTEGER, date TEXT, heure_debut TEXT, heure_fin TEXT, IDcategorie INTEGER, intitule TEXT)")
    connection.commit()

    class DB:
        def __init__(self):
            self.connexion = connection
            self.cursor = connection.cursor()
            self.inserts = self.commits = 0
            self.closed = False
        def ExecuterReq(self, query):
            self.cursor.execute(query)
        def ResultatReq(self):
            return self.cursor.fetchall()
        def ReqInsert(self, table, values, commit=True):
            self.inserts += 1
            if failure and self.inserts == 2:
                raise RuntimeError("injected second insert failure")
            columns, payload = zip(*values)
            self.cursor.execute("INSERT INTO presences (" + ",".join(columns) + ") VALUES (" + ",".join("?" for _ in payload) + ")", payload)
            if commit:
                self.connexion.commit()
        def Commit(self):
            self.commits += 1
            self.connexion.commit()
        def Close(self):
            self.closed = True
            self.connexion.close()

    db = DB()
    method = next(n for n in ast.walk(ast.parse(SOURCE)) if isinstance(n, ast.FunctionDef) and n.name == "SauvegardeNouveau")
    method.decorator_list = []
    module = ast.Module(body=[method], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"GestionDB": SimpleNamespace(DB=lambda: db), "UTILS_Presences": SimpleNamespace(normaliser_intitule_presence=lambda value: value)}
    exec(compile(module, str(PATH), "exec"), namespace)
    control = lambda value: SimpleNamespace(GetValue=lambda: value)
    dialog = SimpleNamespace(dictDonnees={1: (1, "2026-10-09", True), 2: (2, "2026-10-09", True)}, text_heure_debut=control("08:00"), text_heure_fin=control("09:00"), text_intitule=control("qualification"), treeCtrl_categories=SimpleNamespace(GetDataSelection=lambda: 1))
    if failure:
        with pytest.raises(RuntimeError, match="injected second insert failure"):
            namespace["SauvegardeNouveau"](dialog)
    else:
        assert namespace["SauvegardeNouveau"](dialog) == "Ok"
    assert db.closed
    assert db.commits == (0 if failure else 1)
    with closing(sqlite3.connect(database)) as check:
        rows = check.execute("SELECT IDpersonne FROM presences ORDER BY IDpersonne").fetchall()
    assert rows == ([] if failure else [(1,), (2,)])
