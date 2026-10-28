# -*- coding: utf-8 -*-
"""Régressions du clic direct sur les dossiers et onglets wx à chargement différé."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "teamworks/Ctrl/CTRL_Gadget_pb_personnes.py"


def _method(name, scope=None):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "TreeCtrl")
    method = next(n for n in cls.body
                  if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = dict(scope or {})
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=[method], type_ignores=[])
    ), str(SOURCE), "exec"), namespace)
    return namespace[name]


class _Item:
    def IsOk(self):
        return True


class _MouseTree:
    def __init__(self, kind, flags):
        self.flags = flags
        self.target = {"kind": kind, "IDpersonne": 15}
        self._QueueOpenProblem = Mock()

    def HitTest(self, pos):
        return _Item(), self.flags

    def GetItemData(self, item):
        return self.target


def test_single_click_on_person_label_opens_exact_person():
    ct = SimpleNamespace(TREE_HITTEST_ONITEMLABEL=0x40)
    handler = _method("OnTreeMouseUp", {"CT": ct})
    tree = _MouseTree("person", 0x40)
    event = SimpleNamespace(GetPosition=lambda: (1, 2), Skip=Mock())
    handler(tree, event)
    tree._QueueOpenProblem.assert_called_once_with({
        "kind": "person", "IDpersonne": 15
    })
    event.Skip.assert_called_once_with()


def test_single_click_on_alert_or_expander_does_not_open_dialog():
    ct = SimpleNamespace(TREE_HITTEST_ONITEMLABEL=0x40)
    handler = _method("OnTreeMouseUp", {"CT": ct})
    for kind, flag in [
        ("piece", 0x40), ("contract", 0x40),
        ("category", 0x40), ("person", 0x08), ("person", 0x20),
    ]:
        tree = _MouseTree(kind, flag)
        handler(tree, SimpleNamespace(
            GetPosition=lambda: (1, 2), Skip=Mock()
        ))
        tree._QueueOpenProblem.assert_not_called()


def test_activation_keeps_double_click_and_keyboard_with_categories_expandable():
    handler = _method("OnItemActivated")
    item = _Item()
    event = SimpleNamespace(GetItem=lambda: item, Skip=Mock())
    for kind in ("piece", "contract", "person", "information"):
        tree = SimpleNamespace(
            GetItemData=lambda item, kind=kind: {"kind": kind, "IDpersonne": 9},
            _QueueOpenProblem=Mock()
        )
        handler(tree, event)
        tree._QueueOpenProblem.assert_called_once()
    tree = SimpleNamespace(
        GetItemData=lambda item: {"kind": "category", "IDpersonne": 9},
        _QueueOpenProblem=Mock()
    )
    handler(tree, event)
    tree._QueueOpenProblem.assert_not_called()
    event.Skip.assert_called_once()


def test_pending_target_prevents_double_open_and_resets_after_modal():
    scheduled = []
    wx = SimpleNamespace(CallAfter=lambda fn, arg: scheduled.append((fn, arg)))
    queue = _method("_QueueOpenProblem", {"wx": wx})
    run = _method("_RunOpenProblem")
    tree = SimpleNamespace(_opening_target=False, _OpenProblem=Mock())
    tree._RunOpenProblem = lambda target: run(tree, target)
    first = {"kind": "person", "IDpersonne": 12}
    queue(tree, first)
    queue(tree, first)
    assert len(scheduled) == 1
    assert tree._opening_target is True
    fn, target = scheduled.pop()
    fn(target)
    tree._OpenProblem.assert_called_once_with(first)
    assert tree._opening_target is False


def test_guard_clears_when_opening_raises():
    run = _method("_RunOpenProblem")
    tree = SimpleNamespace(
        _opening_target=True, _OpenProblem=Mock(side_effect=RuntimeError("probe"))
    )
    try:
        run(tree, {"kind": "person", "IDpersonne": 12})
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected error from mocked dialog")
    assert tree._opening_target is False


def test_piece_action_waits_for_real_lazy_page_before_opening_editor():
    page = SimpleNamespace(AjouterPiece=Mock())
    notebook = SimpleNamespace(
        GetPageCount=lambda: 8, SetSelection=Mock(), pageStatut=None,
    )
    def load(index):
        assert index == 2
        notebook.pageStatut = page
    notebook.EnsurePageLoaded = Mock(side_effect=load)
    handler = _method("_OpenProblemPage", {"_": lambda text: text})
    handler(None, SimpleNamespace(notebook=notebook), {
        "kind": "piece", "IDtype_piece": 14,
    })
    notebook.SetSelection.assert_called_once_with(2)
    notebook.EnsurePageLoaded.assert_called_once_with(2)
    page.AjouterPiece.assert_called_once_with(IDtypePiece=14)


def test_due_action_waits_for_real_lazy_contract_page_without_auto_receipt():
    contracts = SimpleNamespace(
        GetItemCount=lambda: 2,
        GetItemData=lambda row: (55, 99)[row],
        Select=Mock(), Focus=Mock(), EnsureVisible=Mock()
    )
    page = SimpleNamespace(
        list_ctrl_contrats=contracts, ImprimerDUE=Mock(),
        OnBoutonDue=Mock(), OnBoutonSignature=Mock()
    )
    notebook = SimpleNamespace(
        GetPageCount=lambda: 8, SetSelection=Mock(), pageContrats=None
    )
    def load(index):
        assert index == 3
        notebook.pageContrats = page
    notebook.EnsurePageLoaded = Mock(side_effect=load)
    handler = _method("_OpenProblemPage", {"_": lambda text: text})
    handler(None, SimpleNamespace(notebook=notebook), {
        "kind": "contract", "IDcontrat": 99, "operation": "due",
    })
    notebook.EnsurePageLoaded.assert_called_once_with(3)
    contracts.Select.assert_called_once_with(1)
    page.ImprimerDUE.assert_called_once()
    page.OnBoutonDue.assert_not_called()
    page.OnBoutonSignature.assert_not_called()


def test_tooltips_and_mouse_bindings_match_the_documented_navigation():
    source = SOURCE.read_text(encoding="utf-8")
    assert "self.Bind(wx.EVT_LEFT_UP, self.OnTreeMouseUp)" in source
    assert "self.Bind(CT.EVT_TREE_ITEM_ACTIVATED, self.OnItemActivated)" in source
    assert "flags & CT.TREE_HITTEST_ONITEMLABEL" in source
    assert "if callable(ensure_page) and page_index:" in source
    assert "self.MAJ_treeCtrl()" in source
