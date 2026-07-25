import ast
import io
import token
import tokenize
from pathlib import Path


ROOT = Path("teamworks")
FORBIDDEN_NAMES = {"xrange", "basestring", "unicode", "long", "raw_input", "execfile"}


def read_source(path: Path) -> str:
    data = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
    return data.decode(encoding)


def iter_name_tokens(path: Path):
    source = read_source(path)
    yield from tokenize.generate_tokens(io.StringIO(source).readline)


def test_python2_builtin_names_do_not_return_in_code():
    violations = []

    for path in sorted(ROOT.rglob("*.py")):
        try:
            tokens = iter_name_tokens(path)
            for item in tokens:
                if item.type == token.NAME and item.string in FORBIDDEN_NAMES:
                    violations.append(f"{path}:{item.start[0]}: {item.string}")
        except (SyntaxError, UnicodeDecodeError, tokenize.TokenError):
            continue

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
