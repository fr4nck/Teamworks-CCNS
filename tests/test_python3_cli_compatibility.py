from pathlib import Path
import ast


TEAMWORKS_ROOT = Path("teamworks")
CRYPTAGE_SOURCE = TEAMWORKS_ROOT / "Utils" / "UTILS_Cryptage_fichier.py"


def test_cryptage_cli_uses_python3_input_only():
    source = CRYPTAGE_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "raw_input" not in called_names
    assert "input" in called_names


def test_no_raw_input_call_remains_in_teamworks_sources():
    offenders = []

    for source_path in TEAMWORKS_ROOT.rglob("*.py"):
        source = source_path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "raw_input"
            ):
                offenders.append(f"{source_path}:{node.lineno}")

    assert offenders == []
