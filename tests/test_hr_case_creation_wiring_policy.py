import ast
from pathlib import Path


COCKPIT = Path("teamworks/Dlg/DLG_Demarches_rh.py")
FORM = Path("teamworks/Dlg/DLG_Demarches_rh_creation.py")


def _source(path):
    return path.read_text(encoding="utf-8")


def _tree(path):
    return ast.parse(_source(path), filename=str(path))


def _find_method(path, class_name, method_name):
    for node in _tree(path).body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return child
    raise AssertionError("%s.%s introuvable" % (class_name, method_name))


def test_creation_runtime_and_dialog_stay_lazy_loaded():
    cockpit_tree = _tree(COCKPIT)
    runtime_method = _find_method(COCKPIT, "Dialog", "_get_creation_runtime")
    create_handler = _find_method(COCKPIT, "Dialog", "OnNewCase")

    runtime_imports = [
        alias.name
        for node in ast.walk(runtime_method)
        if isinstance(node, ast.ImportFrom)
        and node.module == "application.bootstrap.hr_case_creation_factory"
        for alias in node.names
    ]
    assert "HrCaseCreationRuntimeFactory" in runtime_imports

    dialog_imports = [
        alias.name
        for node in ast.walk(create_handler)
        if isinstance(node, ast.ImportFrom)
        and node.module == "Dlg"
        for alias in node.names
    ]
    assert "DLG_Demarches_rh_creation" in dialog_imports

    for node in cockpit_tree.body:
        if isinstance(node, ast.ImportFrom):
            assert node.module != "application.bootstrap.hr_case_creation_factory"
            if node.module == "Dlg":
                assert all(alias.name != "DLG_Demarches_rh_creation" for alias in node.names)


def test_new_case_button_is_explicit_and_independent_from_selection():
    source = _source(COCKPIT)
    update_state = ast.unparse(_find_method(COCKPIT, "Dialog", "_update_action_state"))

    assert 'self.new_case = wx.Button(self, -1, _(u"Nouvelle démarche"))' in source
    assert "self.new_case.Bind(wx.EVT_BUTTON, self.OnNewCase)" in source
    assert "self.new_case.Enable" not in update_state


def test_creation_handler_uses_real_people_and_configured_organizations():
    handler = ast.unparse(_find_method(COCKPIT, "Dialog", "OnNewCase"))

    assert "runtime.list_organizations()" in handler
    assert "runtime.list_people()" in handler
    assert "if not organizations" in handler
    assert "people=people" in handler
    assert "organizations=organizations" in handler
    assert "opened_on=opened_on" in handler


def test_creation_requires_dialog_validation_and_explicit_confirmation_before_write():
    handler = ast.unparse(_find_method(COCKPIT, "Dialog", "OnNewCase"))

    assert "dlg.GetRequest()" in handler
    assert "wx.MessageDialog" in handler
    assert "wx.YES_NO" in handler
    assert "confirm.ShowModal() != wx.ID_YES" in handler
    assert "runtime.create(request)" in handler
    assert handler.index("confirm.ShowModal()") < handler.index("runtime.create(request)")
    assert "RefreshData(select_case_id=result.case.case_id)" in handler


def test_creation_handler_does_not_bypass_application_boundary_or_exchange_status():
    handler = ast.unparse(_find_method(COCKPIT, "Dialog", "OnNewCase"))

    for forbidden in (
        "structure_ref",
        "GestionDB",
        "TeamworksHrCaseCreationRepository",
        "save_case(",
        "append_event(",
        "create_case_with_event(",
        "with_exchange_status(",
        "exchange_status",
    ):
        assert forbidden not in handler


def test_form_builds_explicit_creation_request_without_legal_catalog():
    source = _source(FORM)
    build_request = ast.unparse(_find_method(FORM, "Dialog", "BuildRequest"))

    for required in (
        "HrCaseCreationRequest",
        "case_type_code=",
        "case_type_label=",
        "subject_kind=",
        "subject_identifier=",
        "organization_code=",
        "opened_on=",
        "due_on=",
        "expected_documents=",
        "comment=",
    ):
        assert required in build_request

    assert "ExpectedDocument.create" in source
    assert "code | libellé | obligatoire/facultative" in source
    assert "_ACTIVE_STRUCTURE_SUBJECT" in source

    for forbidden in (
        "DPAE",
        "DSN",
        "France Travail",
        "Net-entreprises",
        "requests",
        "webbrowser",
        "socket",
        "subprocess",
        "GestionDB",
    ):
        assert forbidden not in source


def test_form_requires_explicit_required_or_optional_marker_for_each_document():
    source = _source(FORM)

    assert '_REQUIRED_MARKERS = {' in source
    assert '_OPTIONAL_MARKERS = {' in source
    assert 'indiquez explicitement « obligatoire » ou « facultative »' in source
    assert "len(parts) != 3" in source
