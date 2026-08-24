from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRESENCE_SOURCES = (
    ROOT / "teamworks" / "Ctrl" / "CTRL_Presences_personnes.py",
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
    for path in PRESENCE_SOURCES:
        source = path.read_text(encoding="utf-8")
        assert '_PHOENIX = "phoenix" in wx.PlatformInfo' in source, path
        assert '_CheckboxFallback = object if _PHOENIX else CheckListCtrlMixin' in source, path
        assert "if _PHOENIX:" in source, path
        assert "self.EnableCheckBoxes(True)" in source, path
        assert "CheckListCtrlMixin.__init__(self)" in source, path
