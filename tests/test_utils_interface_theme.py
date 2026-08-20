import ast
from pathlib import Path


SOURCE_PATH = Path("teamworks/Utils/UTILS_Interface.py")

REQUIRED_FUNCTIONS = {
    "GetTheme",
    "SetTheme",
    "GetAppearanceMode",
    "SetAppearanceMode",
    "IsSystemDark",
    "ResolveAppearance",
    "GetPalette",
    "GetToken",
    "GetValeur",
}

REQUIRED_TOKENS = {
    "surface",
    "surface_container_lowest",
    "surface_container_low",
    "surface_container",
    "surface_container_high",
    "surface_container_highest",
    "on_surface",
    "on_surface_variant",
    "primary",
    "on_primary",
    "primary_container",
    "on_primary_container",
    "outline",
    "outline_variant",
    "success",
    "warning",
    "danger",
    "info",
    "selection",
    "selection_text",
    "disabled",
    "focus",
}

LEGACY_THEMES = {"Vert", "Bleu", "Noir"}
LEGACY_KEYS = {
    "couleur_tres_foncee",
    "couleur_claire",
    "couleur_tres_claire",
    "couleur_tres_claire_2",
}


def parse_source():
    return ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))


def assignment_value(tree, name):
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                return node.value
    raise AssertionError("Affectation %s introuvable" % name)


def literal_strings(node):
    return {
        item.value
        for item in ast.walk(node)
        if isinstance(item, ast.Constant) and isinstance(item.value, str)
    }


def test_theme_public_api_is_stable():
    tree = parse_source()
    functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert REQUIRED_FUNCTIONS <= functions


def test_semantic_tokens_cover_the_common_design_system():
    tree = parse_source()
    tokens = literal_strings(assignment_value(tree, "SEMANTIC_TOKENS"))
    assert REQUIRED_TOKENS <= tokens


def test_legacy_themes_and_keys_remain_available():
    tree = parse_source()
    donnees = assignment_value(tree, "DONNEES")
    assert isinstance(donnees, ast.Dict)

    themes = {
        key.value
        for key in donnees.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }
    assert LEGACY_THEMES <= themes

    strings = literal_strings(donnees)
    assert LEGACY_KEYS <= strings


def test_light_and_dark_palettes_are_distinct_and_complete():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = parse_source()
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    assert "_build_light_palette" in functions
    assert "_build_dark_palette" in functions

    light_tokens = literal_strings(functions["_build_light_palette"])
    dark_tokens = literal_strings(functions["_build_dark_palette"])
    assert REQUIRED_TOKENS <= light_tokens
    assert REQUIRED_TOKENS <= dark_tokens

    # Le thème sombre doit être une palette dédiée, jamais une inversion globale.
    assert "Invert" not in source
    assert "255 -" not in source


def test_system_light_dark_modes_are_preserved():
    tree = parse_source()
    modes = literal_strings(assignment_value(tree, "APPEARANCE_MODES"))
    assert {"system", "light", "dark"} <= modes
