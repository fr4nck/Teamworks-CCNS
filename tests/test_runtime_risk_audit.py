from pathlib import Path

from scripts.audit_runtime_risks import audit_ast, audit_text, source_lines


def categories_for(line: str) -> set[str]:
    root = Path("/tmp/repo")
    path = root / "teamworks" / "sample.py"
    return {finding.category for finding in audit_text(root, path, [line])}


def missing_handlers(root: Path, path: Path) -> list[str]:
    return [
        finding.detail
        for finding in audit_ast(root, path, source_lines(path))
        if finding.category == "missing-bound-handler"
    ]


def test_sqlite_bytes_path_is_reported_as_priority_risk():
    categories = categories_for("connexion = sqlite3.connect(path.encode('utf-8'))")

    assert "sqlite-direct" in categories
    assert "sqlite-bytes-path" in categories


def test_sqlite_string_path_is_not_reported_as_bytes_risk():
    categories = categories_for("connexion = sqlite3.connect(path)")

    assert "sqlite-direct" in categories
    assert "sqlite-bytes-path" not in categories


def test_bound_handler_inherited_from_project_core_is_accepted(tmp_path):
    dlg = tmp_path / "teamworks" / "Dlg"
    dlg.mkdir(parents=True)
    core = dlg / "sample_core.py"
    wrapper = dlg / "sample.py"

    core.write_text(
        "class Base:\n"
        "    def OnSave(self, event):\n"
        "        pass\n\n"
        "class Panel(Base):\n"
        "    pass\n",
        encoding="utf-8",
    )
    wrapper.write_text(
        "from Dlg import sample_core as CORE\n\n"
        "class Panel(CORE.Panel):\n"
        "    def __init__(self):\n"
        "        self.Bind(None, self.OnSave)\n",
        encoding="utf-8",
    )

    assert missing_handlers(tmp_path, wrapper) == []


def test_genuinely_missing_bound_handler_is_still_reported(tmp_path):
    dlg = tmp_path / "teamworks" / "Dlg"
    dlg.mkdir(parents=True)
    core = dlg / "sample_core.py"
    wrapper = dlg / "sample.py"

    core.write_text(
        "class Panel:\n"
        "    def ExistingHandler(self, event):\n"
        "        pass\n",
        encoding="utf-8",
    )
    wrapper.write_text(
        "from Dlg import sample_core as CORE\n\n"
        "class Panel(CORE.Panel):\n"
        "    def __init__(self):\n"
        "        self.Bind(None, self.DoesNotExist)\n",
        encoding="utf-8",
    )

    assert missing_handlers(tmp_path, wrapper) == ["Panel.DoesNotExist"]
