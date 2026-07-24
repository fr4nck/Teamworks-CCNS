from pathlib import Path
import ast


def test_cryptage_cli_uses_python3_input_only():
    source_path = Path("teamworks/Utils/UTILS_Cryptage_fichier.py")
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "raw_input" not in called_names
    assert "input" in called_names
