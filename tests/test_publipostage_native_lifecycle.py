# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import importlib.util
import threading
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE = ROOT / "teamworks/Dlg/DLG_Publiposteur_lifecycle.py"


def _load_lifecycle():
    spec = importlib.util.spec_from_file_location("dlg_publiposteur_lifecycle_test", LIFECYCLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _class_method_source(class_name, method_name):
    text = LIFECYCLE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == method_name)
    lines = text.splitlines()
    return "\n".join(lines[method.lineno - 1:method.end_lineno])


def test_worker_uses_modern_alive_guard_and_never_touches_wx_directly():
    text = LIFECYCLE.read_text(encoding="utf-8")
    run = _class_method_source("_PublipostageWorker", "run")
    abort = _class_method_source("_PublipostageWorker", "abort")

    assert ".isAlive(" not in text
    assert ".is_alive()" in text
    assert "GetGrandParent" not in run
    assert ".gauge" not in run
    assert ".bouton_" not in run
    assert "wx." not in run
    assert "_post(" in run
    assert "GetGrandParent" not in abort
    assert ".Enable(" not in abort


def test_worker_callbacks_are_marshaled_through_callafter():
    lifecycle = _load_lifecycle()
    calls = []

    class FakeWx:
        @staticmethod
        def CallAfter(callback, *args):
            calls.append((callback, args))

    class FakeModule:
        wx = FakeWx()

    def callback(value):
        raise AssertionError("callback must not execute on worker synchronously")

    lifecycle._post(FakeModule(), callback, 42)
    assert calls == [(callback, (42,))]


def test_abort_is_cooperative_and_safe_for_ten_successive_cycles():
    lifecycle = _load_lifecycle()

    for _ in range(10):
        cancel = threading.Event()
        cont = threading.Event()
        worker = lifecycle._PublipostageWorker(object(), object(), {}, cancel, cont)
        worker.abort()
        assert worker.stop is True
        assert cancel.is_set()
        assert cont.is_set()
        assert worker.is_alive() is False


def test_navigation_and_close_are_blocked_while_worker_is_running():
    text = LIFECYCLE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    install_page = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_install_page_lifecycle"
    )
    body = "\n".join(text.splitlines()[install_page.lineno - 1:install_page.end_lineno])

    assert "wizard.bouton_annuler.Enable(not running)" in body
    assert "wizard.bouton_retour.Enable(not running)" in body
    assert "wizard.EnableCloseButton(not running)" in body
    assert "if _thread_is_alive(thread):" in body
    assert "thread.abort()" in body
    assert "bouton_suite.Enable(False)" in body


def test_com_cleanup_is_idempotent_and_uninitializes_once():
    lifecycle = _load_lifecycle()
    calls = []

    class FakeModule:
        @staticmethod
        def CoUninitialize():
            calls.append("uninit")

    class FakeWord:
        _rc2_finalized = False
        _rc2_com_initialized = True
        doc = None
        Word = None

    publisher = FakeWord()
    lifecycle._finalize_word(FakeModule(), publisher)
    lifecycle._finalize_word(FakeModule(), publisher)

    assert publisher._rc2_finalized is True
    assert publisher._rc2_com_initialized is False
    assert calls == ["uninit"]


def test_runtime_patch_is_loaded_only_for_publiposteur_without_removing_existing_fiche_patch():
    source = (ROOT / "teamworks/Dlg/__init__.py").read_text(encoding="utf-8")
    assert 'name == "DLG_Publiposteur"' in source
    assert "DLG_Publiposteur_lifecycle" in source
    assert "lifecycle.install(module)" in source
    assert 'name == "DLG_Fiche_individuelle"' in source
    assert "lazy.install(module)" in source
    assert "problems.install(module)" in source
    assert "refresh.install(module)" in source
