import ast
import io
import tokenize
from pathlib import Path


ROOT = Path("teamworks")
FORBIDDEN_NAMES = {"xrange", "basestring", "unicode", "long", "raw_input", "execfile"}


def read_source(path: Path) -> str:
    data = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
    return data.decode(encoding)


def test_python2_builtin_names_do_not_return_in_code():
    violations = []

    for path in sorted(ROOT.rglob("*.py")):
        try:
            tree = ast.parse(read_source(path))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in FORBIDDEN_NAMES
            ):
                violations.append(f"{path}:{node.lineno}: {node.func.id}")

            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"isinstance", "issubclass"}
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Name)
                and node.args[1].id in FORBIDDEN_NAMES
            ):
                violations.append(f"{path}:{node.lineno}: {node.args[1].id}")

    assert not violations, "Python 2 builtin names found:\n" + "\n".join(violations)


def test_sys_maxsize_is_backed_by_an_import():
    violations = []

    for path in sorted(ROOT.rglob("*.py")):
        try:
            tree = ast.parse(read_source(path))
        except (SyntaxError, UnicodeDecodeError):
            continue

        uses_sys_maxsize = any(
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "sys"
            and node.attr == "maxsize"
            for node in ast.walk(tree)
        )
        imports_sys = any(
            isinstance(node, ast.Import)
            and any(alias.name == "sys" for alias in node.names)
            for node in tree.body
        )

        if uses_sys_maxsize and not imports_sys:
            violations.append(str(path))

    assert not violations, "sys.maxsize used without import sys:\n" + "\n".join(violations)


def test_python2_and_python3_six_runtime_branches_are_gone():
    violations = []

    for path in sorted(ROOT.rglob("*.py")):
        try:
            tree = ast.parse(read_source(path))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "six"
                and node.attr in {"PY2", "PY3"}
            ):
                violations.append(f"{path}:{node.lineno}: six.{node.attr}")

    assert not violations, "Legacy six runtime branches found:\n" + "\n".join(violations)
