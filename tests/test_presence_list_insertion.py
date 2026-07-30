from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ROOT / "teamworks" / "Dlg" / "DLG_Saisie_presence.py",
    ROOT / "teamworks" / "Ctrl" / "CTRL_Presences.py",
)

FORBIDDEN = (
    "InsertItem(sys.maxsize,",
    "InsertItem(six.MAXSIZE,",
    "InsertStringItem(sys.maxsize,",
    "InsertStringItem(six.MAXSIZE,",
)


def test_presence_lists_use_a_valid_phoenix_append_index() -> None:
    combined = ""
    for path in TARGETS:
        source = path.read_text(encoding="utf-8")
        combined += source
        assert not any(token in source for token in FORBIDDEN), path
        if "CheckListCtrlMixin" in source:
            assert "self.EnableCheckBoxes(True)" in source, path
        compile(source, str(path), "exec")

    assert "InsertItem(self.GetItemCount()," in combined
