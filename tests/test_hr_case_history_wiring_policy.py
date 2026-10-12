import ast
from pathlib import Path


DIALOG = Path("teamworks/Dlg/DLG_Demarches_rh.py")


def _source():
    return DIALOG.read_text(encoding="utf-8")


def _tree():
    return ast.parse(_source(), filename=str(DIALOG))


def _find_method(class_name, method_name):
    for node in _tree().body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return child
    raise AssertionError("%s.%s introuvable" % (class_name, method_name))


def _find_class(class_name):
    for node in _tree().body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise AssertionError("classe %s introuvable" % class_name)


def test_history_component_is_loaded_only_from_explicit_handler():
    tree = _tree()
    handler = _find_method("Dialog", "OnHistory")

    lazy_imports = [
        alias.name
        for node in ast.walk(handler)
        if isinstance(node, ast.ImportFrom)
        and node.module == "Dlg"
        for alias in node.names
    ]
    assert "DLG_Demarches_rh_historique" in lazy_imports

    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "Dlg":
            assert all(
                alias.name != "DLG_Demarches_rh_historique"
                for alias in node.names
            )


def test_no_other_dialog_method_loads_history_component():
    dialog = _find_class("Dialog")
    for method in dialog.body:
        if not isinstance(method, ast.FunctionDef) or method.name == "OnHistory":
            continue
        imported = [
            alias.name
            for node in ast.walk(method)
            if isinstance(node, ast.ImportFrom)
            and node.module == "Dlg"
            for alias in node.names
        ]
        assert "DLG_Demarches_rh_historique" not in imported


def test_history_button_is_selection_scoped_but_available_on_closed_cases():
    source = _source()

    assert 'self.history = wx.Button(self, -1, _(u"Historique"))' in source
    assert "self.history.Enable(False)" in source
    assert "self.history.Enable(has_selection)" in source
    assert "self.history.Bind(wx.EVT_BUTTON, self.OnHistory)" in source

    update_method = ast.unparse(_find_method("Dialog", "_update_action_state"))
    assert "self.history.Enable(has_selection)" in update_method
    assert "self.advance.Enable" in update_method
    assert "HrCaseStatus.ACCEPTED" in update_method
    assert "HrCaseStatus.CANCELLED" in update_method


def test_history_handler_passes_only_case_identifier_to_component():
    handler = ast.unparse(_find_method("Dialog", "OnHistory"))

    assert "case_id=row.case_id" in handler
    assert "structure_ref" not in handler
    assert "GestionDB" not in handler
    assert "HrCaseHistoryRuntimeFactory" not in handler


def test_history_handler_does_not_mutate_case_or_audit_log():
    handler = ast.unparse(_find_method("Dialog", "OnHistory"))

    for forbidden in (
        "transition(",
        "save_case(",
        "append_event(",
        "persist_case_transition(",
        "with_exchange_status(",
        "DeleteItem(",
    ):
        assert forbidden not in handler


def test_existing_workflow_remains_lazy_after_history_wiring():
    method = _find_method("Dialog", "_get_workflow_runtime")
    lazy_imports = [
        alias.name
        for node in ast.walk(method)
        if isinstance(node, ast.ImportFrom)
        and node.module == "application.bootstrap.hr_case_workflow_factory"
        for alias in node.names
    ]

    assert "HrCaseWorkflowRuntimeFactory" in lazy_imports
