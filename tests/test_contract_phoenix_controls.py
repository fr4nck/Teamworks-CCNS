from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_contrat_p4.py"


def test_contract_fields_list_uses_valid_phoenix_insertion() -> None:
    source = TARGET.read_text(encoding="iso-8859-15")

    assert "six.MAXSIZE" not in source
    assert "InsertItem(sys.maxsize," not in source
    assert "InsertStringItem(sys.maxsize," not in source
    assert "InsertItem(self.GetItemCount()," in source
    compile(source, str(TARGET), "exec")


def test_contract_fields_list_enables_phoenix_checkboxes() -> None:
    source = TARGET.read_text(encoding="iso-8859-15")
    marker = (
        "if 'phoenix' in wx.PlatformInfo:\n"
        "            self.EnableCheckBoxes(True)"
    )

    assert source.count(marker) == 1
    assert "CheckListCtrlMixin.__init__(self)" in source
