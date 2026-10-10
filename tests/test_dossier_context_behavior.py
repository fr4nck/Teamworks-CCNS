"""Exercise context invalidation without opening or changing a real database."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import sys
import types


def method(path, class_name, name):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    node = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == name)
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), path, "exec"), namespace)
    return namespace[name]


def test_switch_clears_previous_person_and_filter_without_querying_new_database():
    switch = method("teamworks/Ctrl/CTRL_Personnes.py", "PanelPersonnes", "OnChangementDossier")
    table = SimpleNamespace(selectionID=42, selectionTrack=object(), criteres="old-filter")
    panel = SimpleNamespace(
        init=True, listCtrl_personnes=table, barreRecherche=SimpleNamespace(OnCancel=Mock()),
        AffichePanelResume=Mock(), AfficheLabelSelection=Mock(),
        bouton_modifier=SimpleNamespace(Enable=Mock()), bouton_supprimer=SimpleNamespace(Enable=Mock()),
    )
    switch(panel, "old", "new")
    assert table.selectionID is None and table.selectionTrack is None
    assert table.criteres == ""
    panel.barreRecherche.OnCancel.assert_called_once_with(None)
    panel.AffichePanelResume.assert_called_once_with(False)
    panel.AfficheLabelSelection.assert_called_once_with(False)
    panel.bouton_modifier.Enable.assert_called_once_with(False)
    panel.bouton_supprimer.Enable.assert_called_once_with(False)


def test_same_dossier_preserves_current_selection():
    switch = method("teamworks/Ctrl/CTRL_Personnes.py", "PanelPersonnes", "OnChangementDossier")
    panel = SimpleNamespace(init=True, listCtrl_personnes=SimpleNamespace(selectionID=42))
    switch(panel, "same", "same")
    assert panel.listCtrl_personnes.selectionID == 42


def test_frame_invalidates_caches_before_notifying_pages(monkeypatch):
    invalidate = method("teamworks/Teamworks_core.py", "MyFrame", "InvaliderContexteDossier")
    events = []
    cache = SimpleNamespace(clear_ccns_home_cache=lambda: events.append("cache"))
    package = types.ModuleType("CcnsCore")
    package.home_gadgets_ccns = cache
    monkeypatch.setitem(sys.modules, "CcnsCore", package)
    frame = SimpleNamespace(dictNomsPersonnes={42: "old"}, dictProblemesPersonnes={42: "old"})
    def notify(old, new):
        assert not hasattr(frame, "dictNomsPersonnes")
        assert not hasattr(frame, "dictProblemesPersonnes")
        assert (old, new) == ("old", "new")
        events.append("notify")
    frame.toolBook = SimpleNamespace(OnChangementDossier=notify)
    invalidate(frame, "old", "new")
    assert events == ["cache", "notify"]


def test_modern_navigation_notifies_all_pages_including_hidden_ones():
    notify = method("teamworks/Ctrl/CTRL_Navigation_principale.py", "NavigationPrincipale", "OnChangementDossier")
    calls = []
    pages = [
        SimpleNamespace(OnChangementDossier=lambda a, b: calls.append(("home", a, b))),
        SimpleNamespace(),
        SimpleNamespace(OnChangementDossier=lambda a, b: calls.append(("persons", a, b))),
    ]
    navigation = SimpleNamespace(GetPageCount=lambda: len(pages), GetPage=lambda index: pages[index])
    notify(navigation, "old", "new")
    assert calls == [("home", "old", "new"), ("persons", "old", "new")]
    calls.clear()
    notify(navigation, "same", "same")
    assert calls == []
