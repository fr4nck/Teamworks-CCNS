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


def _imported_modules():
    modules = []
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    return modules


def test_workflow_runtime_is_loaded_only_when_user_requests_an_action():
    tree = _tree()
    method = _find_method("Dialog", "_get_workflow_runtime")

    lazy_imports = [
        alias.name
        for node in ast.walk(method)
        if isinstance(node, ast.ImportFrom)
        and node.module == "application.bootstrap.hr_case_workflow_factory"
        for alias in node.names
    ]
    assert "HrCaseWorkflowRuntimeFactory" in lazy_imports

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            assert node.module != "application.bootstrap.hr_case_workflow_factory"

    init_method = _find_method("Dialog", "__init__")
    init_source = ast.unparse(init_method)
    assert "self._workflow_runtime = None" in init_source
    assert "HrCaseWorkflowRuntimeFactory" not in init_source


def test_workflow_ui_uses_only_application_facades_and_never_persistence():
    source = _source()
    imported = _imported_modules()

    for forbidden_module in (
        "GestionDB",
        "sqlite3",
        "infrastructure.persistence",
        "requests",
        "urllib",
        "webbrowser",
        "socket",
        "subprocess",
    ):
        assert all(
            module != forbidden_module
            and not module.startswith(forbidden_module + ".")
            for module in imported
        )

    for forbidden_call in (
        "save_case(",
        "append_event(",
        "persist_case_transition(",
        "transition_to(",
        "with_exchange_status(",
        "record_manual_status(",
    ):
        assert forbidden_call not in source

    assert "structure_ref" not in source
    assert "workflow.available_transitions(case_id=row.case_id)" in source
    assert "workflow.transition(" in source


def test_ui_never_forges_audit_events_itself():
    source = _source()

    for forbidden in (
        "HrAuditEvent",
        "HrAuditField",
        "HrEventKind",
        "CASE_STATUS_CHANGED",
        "uuid4",
        "datetime.now",
    ):
        assert forbidden not in source


def test_transition_choices_come_from_domain_allowed_statuses():
    source = _source()

    assert "self._allowed_statuses = allowed_statuses" in source
    assert "for status in self._allowed_statuses" in source
    assert "options.allowed_statuses" in source
    assert "_ALLOWED_TRANSITIONS" not in source


def test_displayed_status_is_revalidated_before_transition_dialog():
    source = _source()

    read_marker = "options = workflow.available_transitions(case_id=row.case_id)"
    stale_marker = "if options.case.status is not row.status:"
    dialog_marker = "dlg = TransitionDialog(self, options.case, options.allowed_statuses)"
    assert read_marker in source
    assert stale_marker in source
    assert dialog_marker in source
    assert source.index(read_marker) < source.index(stale_marker) < source.index(dialog_marker)


def test_transition_requires_explicit_confirmation_and_preserves_technical_axis():
    source = _source()

    assert "wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION" in source
    assert "Confirmer le passage" in source
    assert "État technique inchangé" in source
    assert "L'état technique d'échange ne sera pas modifié" in source
    assert "exchange_status=status" not in source
    assert "with_exchange_status" not in source


def test_closed_cases_do_not_offer_action_and_refresh_follows_transition():
    source = _source()

    assert "HrCaseStatus.ACCEPTED" in source
    assert "HrCaseStatus.CANCELLED" in source
    assert "self.advance.Enable" in source
    assert "self.RefreshData(select_case_id=row.case_id)" in source
    assert "modification concurrente" in source


def test_transition_dialog_keeps_result_and_comment_explicit():
    source = _source()

    assert "Résultat / référence" in source
    assert "Commentaire" in source
    assert "result=result" in source
    assert "comment=comment" in source
