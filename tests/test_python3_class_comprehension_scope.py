"""Bloque les références aux attributs de classe invisibles depuis une compréhension Python 3."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "teamworks"
COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def _target_names(target: ast.AST) -> set[str]:
    return {
        node.id
        for node in ast.walk(target)
        if isinstance(node, ast.Name)
    }


def _assigned_names(statement: ast.stmt) -> set[str]:
    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {statement.name}
    if isinstance(statement, ast.Assign):
        return set().union(*(_target_names(target) for target in statement.targets))
    if isinstance(statement, ast.AnnAssign):
        return _target_names(statement.target)
    return set()


def _assignment_value(statement: ast.stmt):
    if isinstance(statement, (ast.Assign, ast.AnnAssign)):
        return statement.value
    return None


def _nested_scope_nodes(comprehension: ast.AST) -> list[ast.AST]:
    generators = comprehension.generators
    nodes = []
    if isinstance(comprehension, ast.DictComp):
        nodes.extend((comprehension.key, comprehension.value))
    else:
        nodes.append(comprehension.elt)
    for index, generator in enumerate(generators):
        if index:
            nodes.append(generator.iter)
        nodes.extend(generator.ifs)
    return nodes


def _unsafe_references(comprehension: ast.AST, class_names: set[str]) -> set[str]:
    bound = set().union(
        *(_target_names(generator.target) for generator in comprehension.generators)
    )
    loaded = {
        node.id
        for root in _nested_scope_nodes(comprehension)
        for node in ast.walk(root)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    return (loaded - bound) & class_names


def test_detector_recognizes_the_preferences_crash_pattern() -> None:
    tree = ast.parse(
        "class Dialog:\n"
        "    LABELS = {'system': 'Système'}\n"
        "    VALUES = [(code, LABELS.get(code)) for code in ('system',)]\n"
    )
    class_node = tree.body[0]
    comprehension = class_node.body[1].value

    assert _unsafe_references(comprehension, {"LABELS"}) == {"LABELS"}


def test_class_comprehensions_do_not_reference_previous_class_attributes() -> None:
    failures = []
    for path in SOURCES.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for class_node in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
            class_names: set[str] = set()
            for statement in class_node.body:
                value = _assignment_value(statement)
                if value is not None:
                    for comprehension in (
                        node for node in ast.walk(value) if isinstance(node, COMPREHENSIONS)
                    ):
                        unsafe = _unsafe_references(comprehension, class_names)
                        if unsafe:
                            failures.append(
                                "%s:%d %s.%s -> %s"
                                % (
                                    path.relative_to(ROOT),
                                    comprehension.lineno,
                                    class_node.name,
                                    type(comprehension).__name__,
                                    ", ".join(sorted(unsafe)),
                                )
                            )
                class_names.update(_assigned_names(statement))

    assert not failures, "Références de portée de classe invalides sous Python 3:\n" + "\n".join(failures)
