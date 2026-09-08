# -*- coding: utf-8 -*-
import ast
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "teamworks" / "Teamworks.py"


def _load_redirect_class():
    text = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    redirect_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Redirect"
    )

    class BaseRedirect:
        pass

    namespace = {"CORE": SimpleNamespace(Redirect=BaseRedirect)}
    module = ast.Module(body=[redirect_node], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["Redirect"]


def test_redirect_exposes_working_flush():
    redirect_class = _load_redirect_class()

    class FakeFile:
        closed = False

        def __init__(self):
            self.flush_count = 0

        def flush(self):
            self.flush_count += 1

    stream = object.__new__(redirect_class)
    stream.filename = FakeFile()

    stream.flush()

    assert stream.filename.flush_count == 1


def test_redirect_flush_is_safe_after_file_close():
    redirect_class = _load_redirect_class()

    class ClosedFile:
        closed = True

        def flush(self):
            raise AssertionError("flush must not be called on a closed journal")

    stream = object.__new__(redirect_class)
    stream.filename = ClosedFile()
    stream.flush()


def test_application_installs_the_flushable_redirect_on_stdout():
    text = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    init = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_initialiser_application"
    )
    body = ast.get_source_segment(text, init)

    assert "sys.stdout = Redirect(nom_journal)" in body
