import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "teamworks/Ol/OL_candidats.py": (
        "ListView",
        {"OnItemSelected", "DeselectionneItem"},
    ),
    "teamworks/Ol/OL_candidatures.py": (
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
    return methods.values()


def test_priority_rh_callbacks_do_not_swallow_every_exception():
    for relative_path, (class_name, method_names) in TARGETS.items():
        for method in _target_methods(relative_path, class_name, method_names):
            handlers = [
                node for node in ast.walk(method) if isinstance(node, ast.ExceptHandler)
            ]
            assert handlers, f"{relative_path}:{method.name} doit garder son fallback"
            assert all(
                handler.type is not None for handler in handlers
            ), f"{relative_path}:{method.name} contient encore un bare except"


def test_priority_rh_callbacks_only_tolerate_missing_widgets():
    for relative_path, (class_name, method_names) in TARGETS.items():
        for method in _target_methods(relative_path, class_name, method_names):
            for handler in (
                node for node in ast.walk(method) if isinstance(node, ast.ExceptHandler)
            ):
                assert isinstance(handler.type, ast.Name)
                assert handler.type.id == "AttributeError"
