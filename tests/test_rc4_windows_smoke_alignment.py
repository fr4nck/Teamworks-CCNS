# -*- coding: utf-8 -*-
"""Garde-fous de cohérence entre les smokes Windows et le runtime wx RC4.

Les échecs CI Windows de RC3 venaient de smokes restés figés sur une ancienne
structure : navigation de l'assistant contrat, onglets de la fiche salarié et
contexte de ListCtrl_champs. Ces tests statiques tournent sans wxPython.
"""

import ast
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
CONTRACT_DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Creation_contrat.py"
CONTRACT_START = ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_contrat_p2.py"
MODEL_PAGE1 = ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_modele_contrat_p1.py"
PERSON_LAZY = ROOT / "teamworks" / "Dlg" / "DLG_Fiche_individuelle_lazy.py"
PERSON_SMOKE = TOOLS / "smoke_secondary_person_dialog.py"
CHECKLIST_SMOKES = (
    TOOLS / "smoke_checklist_controls.py",
    TOOLS / "smoke_secondary_checklists.py",
)


def _source(path):
    return path.read_text(encoding="utf-8")


def _load_function(path, name, namespace=None):
    source = _source(path)
    tree = ast.parse(source, filename=str(path))
    node = next(
        item for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name == name
    )
    namespace = {} if namespace is None else namespace
    module = ast.Module(body=[node], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace[name]


def _load_method(path, class_name, method_name, namespace):
    source = _source(path)
    tree = ast.parse(source, filename=str(path))
    klass = next(
        item for item in tree.body
        if isinstance(item, ast.ClassDef) and item.name == class_name
    )
    node = next(
        item for item in klass.body
        if isinstance(item, ast.FunctionDef) and item.name == method_name
    )
    module = ast.Module(body=[node], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace[method_name]


def test_contract_smokes_only_expect_reachable_wizard_steps() -> None:
    navigation = _load_function(CONTRACT_DIALOG, "_contract_navigation_pages")
    reachable = set(navigation(True)) | set(navigation(False))
    assert reachable == {2}, "le formulaire de contrat n'a qu'un seul écran"

    smokes = [
        path for path in TOOLS.glob("smoke_*.py")
        if "DLG_Creation_contrat" in _source(path)
    ]
    assert len(smokes) >= 3
    for path in smokes:
        expected = {
            int(value)
            for value in re.findall(r"pageVisible == (\d+)", _source(path))
        }
        assert expected <= reachable, (path.name, sorted(expected - reachable))


def test_person_smoke_lists_every_runtime_tab_in_order() -> None:
    lazy = _source(PERSON_LAZY)
    runtime_tabs = ["Généralités"] + re.findall(
        r'\("page\w+", _\(u"([^"]+)"\)', lazy
    )
    smoke = _source(PERSON_SMOKE)
    block = re.search(r"_smoke_expected_pages = \((.*?)\)", smoke, re.S).group(1)
    smoke_tabs = re.findall(r'"([^"]+)"', block)

    assert "Protection sociale" in runtime_tabs
    assert smoke_tabs == runtime_tabs


def test_checklist_smokes_give_model_fields_a_top_level_context() -> None:
    page = _source(MODEL_PAGE1)
    assert "wx.GetTopLevelParent(self).dictChamps" in page

    for path in CHECKLIST_SMOKES:
        source = _source(path)
        assert '_modele_dialog = wx.Dialog(_host, -1, "Smoke modèle de contrat")' in source, path.name
        assert "_modele_dialog.dictChamps = {}" in source, path.name
        assert "ListCtrl_champs(_modele_box)" in source, path.name
        assert "_modele_context" not in source, path.name


class _Radio:
    def __init__(self, value):
        self.value = value

    def GetValue(self):
        return self.value


class _List:
    def __init__(self, index):
        self.index = index

    def GetFirstSelected(self):
        return self.index


class _Page:
    def __init__(self, applied, selected_id):
        self.radio_oui = _Radio(True)
        self.listCtrl_modeles = _List(0)
        self._IDmodele_applique = applied
        self._selected_id = selected_id
        self.applications = []

    def _IDmodele(self, index):
        return self._selected_id

    def AppliquerModele(self, index):
        self.applications.append(index)
        return True


def test_contract_start_does_not_reapply_displayed_model_on_next() -> None:
    validation = _load_method(CONTRACT_START, "Page", "Validation", {"wx": None, "_": str})

    displayed = _Page(applied=7, selected_id=7)
    assert validation(displayed) is True
    assert displayed.applications == []

    changed = _Page(applied=7, selected_id=9)
    assert validation(changed) is True
    assert changed.applications == [0]


def test_contract_start_applies_model_as_soon_as_it_is_selected() -> None:
    source = _source(CONTRACT_START)

    assert "self.parent.OnModeleSelectionne(event.GetIndex())" in source
    assert "self._IDmodele_applique = IDmodele" in source
    assert "wx.CallAfter(self.MAJ_ListCtrl)" in source
