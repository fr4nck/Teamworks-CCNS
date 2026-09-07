"""Outils de caractérisation statique du code wxPython historique.

Les modules visés importent wxPython et ouvrent des bases pendant la construction des
boîtes de dialogue. Les tests lisent donc leur AST sans les importer : ils figent le
comportement observable avant extraction vers une couche métier testable.
"""

from __future__ import annotations

import ast
import copy
import tokenize
from pathlib import Path
from types import FunctionType
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]


def read_source(relative_path: str) -> str:
    path = REPO_ROOT / relative_path
    # Respecte l'encodage PEP 263 déclaré par les modules historiques.
    with tokenize.open(path) as stream:
        return stream.read()


def parse_module(relative_path: str) -> ast.Module:
    return ast.parse(read_source(relative_path), filename=relative_path)


def class_node(relative_path: str, class_name: str) -> ast.ClassDef:
    for node in parse_module(relative_path).body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise AssertionError(f"Classe {class_name!r} introuvable dans {relative_path}")


def function_node(
    relative_path: str,
    function_name: str,
    *,
    class_name: str | None = None,
) -> ast.FunctionDef:
    body: list[ast.stmt]
    if class_name is None:
        body = parse_module(relative_path).body
    else:
        body = class_node(relative_path, class_name).body

    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            if isinstance(node, ast.AsyncFunctionDef):
                raise AssertionError("Les méthodes historiques ciblées ne doivent pas être async")
            return node
    owner = class_name or "module"
    raise AssertionError(
        f"Fonction {owner}.{function_name} introuvable dans {relative_path}"
    )


def function_source(
    relative_path: str,
    function_name: str,
    *,
    class_name: str | None = None,
) -> str:
    source = read_source(relative_path)
    node = function_node(relative_path, function_name, class_name=class_name)
    segment = ast.get_source_segment(source, node)
    if segment is None:
        raise AssertionError(
            f"Impossible d'extraire {class_name or 'module'}.{function_name}"
        )
    return segment


def compact_whitespace(text: str) -> str:
    return " ".join(text.split())


def load_method_as_function(
    relative_path: str,
    class_name: str,
    method_name: str,
    *,
    globals_: Mapping[str, Any] | None = None,
) -> FunctionType:
    """Compile isolément une méthode pure ou pilotable par doublures.

    La méthode conserve son paramètre ``self``. Aucun import du module wxPython n'est
    exécuté ; seules les dépendances globales explicitement fournies sont disponibles.
    """

    node = copy.deepcopy(
        function_node(relative_path, method_name, class_name=class_name)
    )
    node.decorator_list = []
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace: dict[str, Any] = dict(globals_ or {})
    exec(compile(module, relative_path, "exec"), namespace)
    result = namespace[method_name]
    if not isinstance(result, FunctionType):
        raise AssertionError(f"{method_name} n'a pas produit de fonction")
    return result


def db_data_schema(table_name: str) -> list[tuple[Any, ...]]:
    """Lit une entrée littérale de ``DB_DATA`` sans importer DATA_Tables."""

    relative_path = "teamworks/Data/DATA_Tables.py"
    for node in parse_module(relative_path).body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == "DB_DATA" for target in targets):
            continue
        value = ast.literal_eval(node.value)
        try:
            schema = value[table_name]
        except KeyError as exc:
            raise AssertionError(
                f"Table {table_name!r} absente de DB_DATA"
            ) from exc
        return list(schema)
    raise AssertionError("Affectation littérale DB_DATA introuvable")


def column_names(table_name: str) -> list[str]:
    return [str(column[0]) for column in db_data_schema(table_name)]
