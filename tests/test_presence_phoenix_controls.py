from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRESENCE_SOURCES = (
    ROOT / "teamworks" / "Ctrl" / "CTRL_Presences.py",
    ROOT / "teamworks" / "Dlg" / "DLG_Saisie_presence.py",
)


def test_presence_lists_use_valid_end_insertion_index() -> None:
    forbidden = (
        "InsertItem(six.MAXSIZE,",
        "InsertItem(sys.maxsize,",
        "InsertStringItem(six.MAXSIZE,",
        "InsertStringItem(sys.maxsize,",
    )

    combined = ""
    for path in PRESENCE_SOURCES:
        source = path.read_text(encoding="utf-8")
        combined += source
        for token in forbidden:
            assert token not in source, (path, token)
        compile(source, str(path), "exec")

    assert "InsertItem(self.GetItemCount()," in combined


def test_presence_lists_enable_native_phoenix_checkboxes() -> None:
    marker = (
        "if 'phoenix' in wx.PlatformInfo:\n"
        "            self.EnableCheckBoxes(True)"
    )

    for path in PRESENCE_SOURCES:
        source = path.read_text(encoding="utf-8")
        assert source.count(marker) == 1, path
        assert "CheckListCtrlMixin.__init__(self)" in source
