# -*- coding: utf-8 -*-
"""Clic ciblé sur les alertes de dossiers : aucune donnée privée requise."""
import ast
import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
PERFORMANCE = ROOT / "teamworks/Utils/UTILS_Personnes_performance.py"
TREE = ROOT / "teamworks/Ctrl/CTRL_Gadget_pb_personnes.py"


def _source_function(path, name, namespace, class_name=None):
    module = ast.parse(path.read_text(encoding="utf-8"))
    nodes = module.body
    if class_name:
        nodes = next(node for node in nodes if isinstance(node, ast.ClassDef)
                     and node.name == class_name).body
    func = next(node for node in nodes if isinstance(node, ast.FunctionDef)
                and node.name == name)
    compiled = ast.Module(body=[func], type_ignores=[])
    scope = dict(namespace)
    exec(compile(ast.fix_missing_locations(compiled), str(path), "exec"), scope)
    return scope[name]


class DummyDB:
    def __init__(self):
        self.calls = []
        self.rows = []

    def ExecuterReq(self, query):
        self.calls.append(query)
        today = datetime.date.today()
        expires = (today + datetime.timedelta(days=7)).isoformat()
        start = (today - datetime.timedelta(days=14)).isoformat()
        if "FROM personnes WHERE" in query:
            self.rows = [(101, "Mme", "EXEMPLE", None, "Alice",
                          "1999-05-12", "35000", "Rennes", 1, 1,
                          "2222222222222", "1 rue Exemple", "35000",
                          "Rennes", 1)]
        elif "FROM coordonnees" in query:
            self.rows = [(101,)]
        elif "FROM diplomes\n" in query:
            self.rows = [(101, 6, "Diplôme B.A.F.A.")]
        elif "FROM diplomes_pieces\n" in query:
            self.rows = [(8, "Certificat médical")]
        elif "LEFT JOIN pieces" in query:
            self.rows = [(101, 8, start, expires)]
        elif "FROM contrats\n" in query:
            self.rows = [(101, 1001, "", "Non"), (101, 1002, "Oui", "")]
        else:
            raise AssertionError("Requête inattendue : " + query)

    def ResultatReq(self):
        return list(self.rows)


def _search():
    return _source_function(PERFORMANCE, "Recherche_problemes_personnes", {
        "_ids_uniques": lambda values: list(dict.fromkeys(values)),
        "_clause_ids": lambda values: "(%s)" % ",".join(map(str, values)),
        "datetime": datetime,
        "_": lambda text: text,
    })


def test_tree_alerts_resolve_exact_person_piece_and_contract_ids():
    db = DummyDB()
    names, problems, targets = _search()((101,), DB=db, include_targets=True)
    assert len(db.calls) == 6
    assert names[101] == "EXEMPLE Alice"
    by_name = {
        label: target
        for category, labels in problems[101].items()
        for label, target in zip(labels, targets[101][category])
    }
    assert by_name["Nom de jeune fille"] == {
        "kind": "information", "field": "Nom de jeune fille"
    }
    assert by_name["Diplôme B.A.F.A."] == {
        "kind": "piece", "IDtype_piece": 6, "state": "missing"
    }
    assert by_name["Certificat médical"] == {
        "kind": "piece", "IDtype_piece": 8, "state": "expiring"
    }
    contract_rows = [
        target for cat, labels in problems[101].items()
        for label, target in zip(labels, targets[101][cat])
        if label in ("Contrat non signé", "DUE à faire")
    ]
    assert contract_rows == [
        {"kind": "contract", "IDcontrat": 1001, "operation": "signature"},
        {"kind": "contract", "IDcontrat": 1001, "operation": "due"},
        {"kind": "contract", "IDcontrat": 1002, "operation": "due"},
    ]


def test_default_problem_api_remains_two_values_for_existing_callers():
    names, problems = _search()((101,), DB=DummyDB())
    assert 101 in names
    assert problems[101]


def test_tree_stores_id_metadata_not_guessed_labels():
    source = TREE.read_text(encoding="utf-8")
    assert "CT.EVT_TREE_ITEM_ACTIVATED" in source
    assert "CT.EVT_TREE_ITEM_GETTOOLTIP" in source
    assert "SetItemData(newItem, item[2] if len(item) > 2 else None)" in source
    assert "Creation_liste_pb_personnes(include_targets=True)" in source
    assert "target[\"IDpersonne\"] = IDpersonne" in source
    assert "self._GetCategoryLabel(nomCategorie, valeurs)" in source
    assert "wx.CallAfter(self._OpenProblemPage, dialog, dict(target))" in source


def test_known_missing_person_field_focuses_exact_input():
    control = SimpleNamespace(IsEnabled=lambda: True, SetFocus=Mock())
    general = SimpleNamespace(text_ctrl_nomjf=control)
    notebook = SimpleNamespace(
        GetPageCount=lambda: 4, SetSelection=Mock(), pageGeneralites=general,
    )
    handler = _source_function(TREE, "_OpenProblemPage", {
        "_": lambda x: x,
    }, class_name="TreeCtrl")
    handler(None, SimpleNamespace(notebook=notebook), {
        "kind": "information", "field": "Nom de jeune fille",
    })
    notebook.SetSelection.assert_called_once_with(0)
    control.SetFocus.assert_called_once_with()


def test_unknown_person_field_opens_general_tab_without_invalid_getattr():
    notebook = SimpleNamespace(
        GetPageCount=lambda: 4, SetSelection=Mock(), pageGeneralites=object(),
    )
    handler = _source_function(TREE, "_OpenProblemPage", {
        "_": lambda x: x,
    }, class_name="TreeCtrl")
    handler(None, SimpleNamespace(notebook=notebook), {
        "kind": "information", "field": "Nationalité",
    })
    notebook.SetSelection.assert_called_once_with(0)


def test_missing_document_opens_prefilled_editor_without_auto_receipt():
    page = SimpleNamespace(AjouterPiece=Mock())
    notebook = SimpleNamespace(
        GetPageCount=lambda: 8, SetSelection=Mock(), pageStatut=page,
    )
    handler = _source_function(TREE, "_OpenProblemPage", {
        "_": lambda x: x,
    }, class_name="TreeCtrl")
    handler(None, SimpleNamespace(notebook=notebook), {
        "kind": "piece", "IDtype_piece": 6,
    })
    notebook.SetSelection.assert_called_once_with(2)
    page.AjouterPiece.assert_called_once_with(IDtypePiece=6)


class FakeContracts:
    def __init__(self):
        self.selected = None
        self.Select = Mock(side_effect=lambda idx: setattr(self, "selected", idx))
        self.Focus = Mock()
        self.EnsureVisible = Mock()

    def GetItemCount(self):
        return 3

    def GetItemData(self, index):
        return (700, 900, 800)[index]

    def GetItem(self, index, col):
        assert index == 2 and col == 4
        return SimpleNamespace(GetText=lambda: "")


def test_signature_acts_only_on_selected_contract_after_confirmation():
    contracts = FakeContracts()
    page = SimpleNamespace(
        list_ctrl_contrats=contracts,
        OnBoutonSignature=Mock(),
        ImprimerDUE=Mock(),
    )
    notebook = SimpleNamespace(
        GetPageCount=lambda: 4, SetSelection=Mock(), pageContrats=page,
    )
    yes, no = 42, 43
    state = {"decision": no}
    modal = SimpleNamespace(
        ShowModal=lambda: state["decision"], Destroy=Mock(),
    )
    wx = SimpleNamespace(
        YES_NO=0x01, NO_DEFAULT=0x02, ICON_QUESTION=0x04,
        ID_YES=yes, MessageDialog=lambda *a, **kw: modal,
    )
    handler = _source_function(TREE, "_OpenProblemPage", {
        "wx": wx, "_": lambda x: x,
    }, class_name="TreeCtrl")
    target = {"kind": "contract", "IDcontrat": 800, "operation": "signature"}
    handler(None, SimpleNamespace(notebook=notebook), target)
    assert contracts.selected == 2
    page.OnBoutonSignature.assert_not_called()
    state["decision"] = yes
    handler(None, SimpleNamespace(notebook=notebook), target)
    page.OnBoutonSignature.assert_called_once_with(None)
    page.ImprimerDUE.assert_not_called()


def test_due_opens_form_but_never_marks_it_as_filed():
    contracts = FakeContracts()
    page = SimpleNamespace(
        list_ctrl_contrats=contracts, ImprimerDUE=Mock(),
        OnBoutonDue=Mock(), OnBoutonSignature=Mock(),
    )
    notebook = SimpleNamespace(
        GetPageCount=lambda: 4, SetSelection=Mock(), pageContrats=page,
    )
    handler = _source_function(TREE, "_OpenProblemPage", {
        "_": lambda x: x,
    }, class_name="TreeCtrl")
    handler(None, SimpleNamespace(notebook=notebook), {
        "kind": "contract", "IDcontrat": 800, "operation": "due",
    })
    assert contracts.selected == 2
    page.ImprimerDUE.assert_called_once_with()
    page.OnBoutonDue.assert_not_called()
    page.OnBoutonSignature.assert_not_called()
