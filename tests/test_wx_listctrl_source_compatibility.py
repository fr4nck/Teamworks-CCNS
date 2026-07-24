from pathlib import Path
import ast


TEAMWORKS_ROOT = Path("teamworks")
OBJECT_LIST_VIEW_SOURCE = TEAMWORKS_ROOT / "ObjectListView" / "ObjectListView.py"


def _attribute_calls(source_path: Path) -> list[tuple[str, int]]:
    source = source_path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source)
    return [
        (node.func.attr, node.lineno)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]


def test_object_list_view_uses_insert_item_api():
    calls = _attribute_calls(OBJECT_LIST_VIEW_SOURCE)
    called_names = {name for name, _ in calls}

    assert "InsertItem" in called_names
    assert "InsertStringItem" not in called_names


def test_no_insert_string_item_call_remains_in_teamworks_sources():
    offenders = []

    for source_path in TEAMWORKS_ROOT.rglob("*.py"):
        try:
            calls = _attribute_calls(source_path)
        except SyntaxError:
            continue

        offenders.extend(
            f"{source_path}:{line}"
            for name, line in calls
            if name == "InsertStringItem"
        )

    assert offenders == []
