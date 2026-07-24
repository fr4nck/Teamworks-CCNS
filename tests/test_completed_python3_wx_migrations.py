import io
from pathlib import Path
import tokenize


COMPLETED_MIGRATIONS = {
    Path("teamworks/Utils/UTILS_Cryptage_fichier.py"): {"raw_input"},
    Path("teamworks/ObjectListView/ObjectListView.py"): {
        "InsertStringItem",
        "SetStringItem",
    },
    Path("teamworks/Ctrl/CTRL_Bouton_image.py"): {"EmptyImage"},
    Path("teamworks/Ctrl/CTRL_Liste_fichiers.py"): {"EmptyBitmap"},
}


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

    for source_path, forbidden_names in COMPLETED_MIGRATIONS.items():
        source = source_path.read_text(encoding="utf-8", errors="replace")
        for name, line_number in tokenized_names(source):
            if name in forbidden_names:
                findings.append(f"{source_path}:{line_number}: {name}")

    assert findings == [], "Anciennes API réintroduites:\n" + "\n".join(findings)
