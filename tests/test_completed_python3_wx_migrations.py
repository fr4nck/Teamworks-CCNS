import io
from pathlib import Path
import tokenize


TEAMWORKS_ROOT = Path("teamworks")
FORBIDDEN_NAMES = {"raw_input", "InsertStringItem", "SetStringItem"}


def iter_python_sources():
    yield from sorted(TEAMWORKS_ROOT.rglob("*.py"))


def tokenized_names(source: str):
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type == tokenize.NAME:
                yield token.string, token.start[0]
    except (IndentationError, SyntaxError, tokenize.TokenError):
        return


def test_completed_python3_and_wx_migrations_do_not_regress():
    findings = []

    for source_path in iter_python_sources():
        source = source_path.read_text(encoding="utf-8", errors="replace")
        for name, line_number in tokenized_names(source):
            if name in FORBIDDEN_NAMES:
                findings.append(f"{source_path}:{line_number}: {name}")

    assert findings == [], "Anciennes API réintroduites:\n" + "\n".join(findings)
