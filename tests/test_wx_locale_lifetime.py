import ast
import gc
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import weakref

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "teamworks/Utils/UTILS_Locale.py"


def load_locale(monkeypatch, app, factory):
    monkeypatch.setitem(sys.modules, "wx", SimpleNamespace(
        GetApp=lambda: app, Locale=factory, LANGUAGE_FRENCH=1,
    ))
    spec = importlib.util.spec_from_file_location("locale_lifetime_test", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_locale_survives_window_references_and_is_shared(monkeypatch):
    created = []

    class Locale:
        def __init__(self, language):
            created.append(language)

    app = SimpleNamespace()
    module = load_locale(monkeypatch, app, Locale)
    window_locale = module.GetLocaleFrancais()
    reference = weakref.ref(window_locale)
    del window_locale
    gc.collect()
    assert reference() is not None
    assert module.GetLocaleFrancais() is reference()
    assert created == [1]


def test_locale_requires_active_application(monkeypatch):
    module = load_locale(monkeypatch, None, lambda language: pytest.fail("created"))
    with pytest.raises(RuntimeError, match="application wx active"):
        module.GetLocaleFrancais()


def test_native_locale_is_created_only_by_application_owner():
    offenders = []
    for path in (ROOT / "teamworks").rglob("*.py"):
        if path == MODULE:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "wx" and node.func.attr == "Locale"):
                offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, offenders
