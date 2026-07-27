import ast
from pathlib import Path


SOURCE_PATH = Path("teamworks/Utils/UTILS_Config.py")

REQUIRED_MODULE_FUNCTIONS = {
    "GetNomFichierConfig",
    "IsFichierExists",
    "GenerationFichierConfig",
    "SupprimerFichier",
    "GetParametre",
    "SetParametre",
    "GetParametres",
    "SetParametres",
}

REQUIRED_CLASS_METHODS = {
    "__init__",
    "GetDictConfig",
    "SetDictConfig",
    "GetItemConfig",
    "SetItemConfig",
    "SetItemsConfig",
    "DelItemConfig",
}


def parse_source() -> ast.Module:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    return ast.parse(source)


def test_public_configuration_functions_are_present():
    tree = parse_source()
    functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert REQUIRED_MODULE_FUNCTIONS <= functions


def test_configuration_class_keeps_its_public_methods():
    tree = parse_source()
    config_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "FichierConfig"
    )
    methods = {
        node.name
        for node in config_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert REQUIRED_CLASS_METHODS <= methods


def test_configuration_module_has_no_python2_runtime_branch():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "six.PY2" not in source
    assert "six.PY3" not in source
    assert "import six" not in source


def test_configuration_api_has_no_mutable_default_arguments():
    tree = parse_source()
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    offenders = []
    for function in functions:
        defaults = list(function.args.defaults) + [
            default
            for default in function.args.kw_defaults
            if default is not None
        ]
        if any(isinstance(default, (ast.Dict, ast.List, ast.Set)) for default in defaults):
            offenders.append(function.name)

    assert offenders == []
