import ast
from pathlib import Path


COCKPIT = Path("teamworks/Dlg/DLG_Demarches_rh.py")
DIALOG = Path("teamworks/Dlg/DLG_Demarches_rh_pieces.py")


def _source(path):
    return path.read_text(encoding="utf-8")


def _imports(path):
    modules = []
    tree = ast.parse(_source(path), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    return modules


def test_document_dialog_does_not_know_persistence_or_file_io():
    source = _source(DIALOG)
    imported = _imports(DIALOG)

    for forbidden in (
        "GestionDB",
        "sqlite3",
        "infrastructure.persistence",
        "pathlib",
        "shutil",
        "tempfile",
        "requests",
        "urllib",
        "webbrowser",
        "socket",
        "subprocess",
    ):
        assert all(
            module != forbidden and not module.startswith(forbidden + ".")
            for module in imported
        )

    assert "wx.FileDialog" not in source
    assert "open(" not in source
    assert "read_bytes" not in source
    assert "write_bytes" not in source


def test_document_runtime_is_loaded_only_when_document_dialog_needs_it():
    source = _source(DIALOG)
    lines = source.splitlines()
    runtime_import = next(
        index
        for index, line in enumerate(lines)
        if "from application.bootstrap.hr_case_documents_factory import (" in line
    )
    get_runtime = next(
        index for index, line in enumerate(lines) if line.startswith("    def _get_runtime(")
    )

    assert runtime_import > get_runtime
    assert "HrCaseDocumentTrackingRuntimeFactory" in source
    assert "self._runtime = factory().create()" in source


def test_document_actions_remain_explicit_audited_business_calls():
    source = _source(DIALOG)

    assert "def OnReceived(" in source
    assert "def OnWithdraw(" in source
    assert ".record_received(" in source
    assert ".withdraw_received(" in source
    assert "wx.MessageDialog(" in source
    assert "wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION" in source
    assert "Réception administrative enregistrée et journalisée" in source
    assert "Retrait administratif enregistré et journalisé" in source


def test_document_ui_never_claims_validation_or_compliance():
    source = _source(DIALOG)

    assert "ne valide ni l'authenticité" in source
    assert "ni la validité, ni la conformité" in source
    assert "Suivi administratif uniquement" in source
    assert "Aucun fichier ni chemin local n'est enregistré" in source


def test_closed_case_is_presented_read_only_and_backend_remains_authoritative():
    source = _source(DIALOG)

    assert "self._read_only = bool(read_only)" in source
    assert "lecture seule : démarche clôturée" in source
    assert "writable = row is not None and not self._read_only" in source
    assert "if row is None or self._read_only:" in source
    assert "if row is None or self._read_only or not row.received:" in source


def test_cockpit_wiring_stays_lazy_and_only_passes_case_identity_and_read_only_state():
    source = _source(COCKPIT)

    assert "self.documents = wx.Button" in source
    assert "self.documents.Bind(wx.EVT_BUTTON, self.OnDocuments)" in source
    assert "def OnDocuments(" in source
    assert "from Dlg import DLG_Demarches_rh_pieces" in source
    assert "case_id=row.case_id" in source
    assert "read_only=row.status in {" in source
    assert "HrCaseStatus.ACCEPTED" in source
    assert "HrCaseStatus.CANCELLED" in source
    assert "application.bootstrap.hr_case_documents_factory" not in source
    assert "GestionDB" in source  # seulement dans la docstring de frontière
    assert "import GestionDB" not in source
