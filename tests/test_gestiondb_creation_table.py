"""CreationTable must compile complete legacy DDL before SQL execution."""

import ast
from pathlib import Path

from infrastructure.persistence.legacy_table_ddl import legacy_create_table_query


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "teamworks" / "GestionDB.py"


def test_creation_table_builds_complete_sql_before_execution():
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    cls = next(node for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == "DB")
    method = next(node for node in cls.body
                  if isinstance(node, ast.FunctionDef) and node.name == "CreationTable")
    compiling = [
        node for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "legacy_create_table_query"
    ]
    execution = [
        node for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "execute"
    ]
    assert len(compiling) == 1
    assert len(execution) == 1
    assert compiling[0].lineno < execution[0].lineno
    assert 'GestionDB.CreationTable' in ast.get_source_segment(source, method)
    assert legacy_create_table_query(
        "demo",
        [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
         ("nom", "VARCHAR(100)")],
        is_network=False,
    ) == "CREATE TABLE demo (id INTEGER PRIMARY KEY AUTOINCREMENT, nom VARCHAR(100))"
