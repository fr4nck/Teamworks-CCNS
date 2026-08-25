import ast
import sqlite3
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "teamworks" / "GestionDB.py"


def _method(name):
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SOURCE_PATH))
    db_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "DB"
    )
    node = next(
        item for item in db_class.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name
    )
    lines = source.splitlines(keepends=True)
    method_source = textwrap.dedent("".join(lines[node.lineno - 1:node.end_lineno]))
    namespace = {}
    exec(compile(method_source, str(SOURCE_PATH), "exec"), namespace)
    return namespace[name]


def test_reqinsert_returns_none_instead_of_masking_sql_error():
    req_insert = _method("ReqInsert")

    class Cursor:
        def execute(self, *_args, **_kwargs):
            raise RuntimeError("échec SQL simulé")

    class FakeDB:
        isNetwork = False
        cursor = Cursor()

        def Commit(self):
            raise AssertionError("Commit ne doit pas être appelé après un INSERT en échec")

    assert req_insert(FakeDB(), "demo", [("nom", "x")]) is None


def test_supprchamp_preserves_columns_after_target_and_their_data():
    suppr_champ = _method("SupprChamp")
    connexion = sqlite3.connect(":memory:")
    connexion.execute(
        "CREATE TABLE demo (id INTEGER, avant TEXT, cible TEXT, apres INTEGER)"
    )
    connexion.execute(
        "INSERT INTO demo (id, avant, cible, apres) VALUES (?, ?, ?, ?)",
        (1, "A", "X", 42),
    )
    connexion.commit()

    class FakeDB:
        isNetwork = False

        def __init__(self, connexion):
            self.connexion = connexion
            self.cursor = connexion.cursor()

        def GetListeChamps2(self, nom_table):
            self.cursor.execute("PRAGMA table_info('%s');" % nom_table)
            return [(row[1], row[2]) for row in self.cursor.fetchall()]

    db = FakeDB(connexion)
    suppr_champ(db, "demo", "cible")

    colonnes = [
        row[1]
        for row in connexion.execute("PRAGMA table_info('demo')").fetchall()
    ]
    assert colonnes == ["id", "avant", "apres"]
    assert connexion.execute(
        "SELECT id, avant, apres FROM demo"
    ).fetchall() == [(1, "A", 42)]
    connexion.close()


def test_supprchamp_refuses_unknown_or_only_column():
    suppr_champ = _method("SupprChamp")

    class Cursor:
        def __init__(self):
            self.scripts = []

        def executescript(self, script):
            self.scripts.append(script)

    class FakeDB:
        isNetwork = False

        def __init__(self, columns):
            self.columns = columns
            self.cursor = Cursor()

        def GetListeChamps2(self, _nom_table):
            return list(self.columns)

    unknown = FakeDB([("id", "INTEGER"), ("nom", "TEXT")])
    assert suppr_champ(unknown, "demo", "absent") is False
    assert unknown.cursor.scripts == []

    only = FakeDB([("id", "INTEGER")])
    assert suppr_champ(only, "demo", "id") is False
    assert only.cursor.scripts == []
