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


def test_cryptage_has_no_six_runtime_dependency():
    source = CRYPTAGE_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    six_attributes = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "six"
    ]

    assert "six" not in imported_modules
    assert six_attributes == []


def test_cryptage_normalizes_text_and_bytes_keys():
    source = CRYPTAGE_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    helper = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_as_bytes"
    )

    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "isinstance"
        for node in ast.walk(helper)
    )
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "encode"
        for node in ast.walk(helper)
    )


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
