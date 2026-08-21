import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "teamworks/Ol/OL_candidats_core.py": (
        "ListView",
        {"OnItemSelected", "DeselectionneItem"},
    ),
    "teamworks/Ol/OL_candidatures_core.py": (
        "ListView",
        {"OnItemSelected", "DeselectionneItem"},
    ),
    "teamworks/Dlg/DLG_Saisie_presence.py": (
        "Panel",
        {"OnBoutonAnnuler", "OnBoutonOk"},
    ),
}


def _target_methods(relative_path, class_name, method_names):
    source = (ROOT / relative_path).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=relative_path)
    target_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    methods = {
        node.name: node
        for node in target_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in method_names
    }
    assert set(methods) == method_names
    return methods


def _bare_except_count(method):
    return sum(
        1
        for node in ast.walk(method)
        if isinstance(node, ast.ExceptHandler) and node.type is None
    )


def test_priority_rh_bare_except_inventory_does_not_grow():
    inventory = {}
    for relative_path, (class_name, method_names) in TARGETS.items():
        methods = _target_methods(relative_path, class_name, method_names)
        inventory[relative_path] = {
            name: _bare_except_count(method)
            for name, method in methods.items()
        }

    assert inventory == {
        "teamworks/Ol/OL_candidats_core.py": {
            "OnItemSelected": 1,
            "DeselectionneItem": 1,
        },
        "teamworks/Ol/OL_candidatures_core.py": {
            "OnItemSelected": 1,
            "DeselectionneItem": 1,
        },
        "teamworks/Dlg/DLG_Saisie_presence.py": {
            "OnBoutonAnnuler": 0,
            "OnBoutonOk": 0,
        },
    }


def test_priority_rh_bare_except_total_is_four():
    total = 0
    for relative_path, (class_name, method_names) in TARGETS.items():
        for method in _target_methods(relative_path, class_name, method_names).values():
            total += _bare_except_count(method)
    assert total == 4
