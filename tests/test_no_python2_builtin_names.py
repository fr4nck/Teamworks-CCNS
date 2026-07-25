import io
import token
import tokenize
from pathlib import Path


ROOT = Path("teamworks")
FORBIDDEN_NAMES = {"xrange", "basestring", "unicode", "long", "raw_input", "execfile"}


def iter_name_tokens(path: Path):
    data = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
    source = data.decode(encoding)
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
