from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIST_TARGET = ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_contrat_p4.py"
SIZER_TARGETS = (
    ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_contrat_p5.py",
    ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_modele_contrat_p2.py",
)


def test_contract_fields_list_uses_valid_phoenix_insertion() -> None:
    source = LIST_TARGET.read_text(encoding="utf-8")

    assert "six.MAXSIZE" not in source
    assert "InsertItem(sys.maxsize," not in source
    assert "InsertStringItem(sys.maxsize," not in source
    assert "InsertItem(self.GetItemCount()," in source
    compile(source, str(LIST_TARGET), "exec")


def test_contract_fields_list_enables_phoenix_checkboxes() -> None:
    source = LIST_TARGET.read_text(encoding="utf-8")

    assert source.count("self.EnableCheckBoxes(True)") == 1
    assert "'phoenix' in wx.PlatformInfo" not in source
    assert '"phoenix" in wx.PlatformInfo' not in source
    assert "CheckListCtrlMixin.__init__(self)" in source


def test_dynamic_contract_fields_do_not_mix_expand_and_vertical_alignment() -> None:
    forbidden = "wx.ALIGN_CENTER_VERTICAL|wx.EXPAND"

    for path in SIZER_TARGETS:
        source = path.read_text(encoding="iso-8859-15")
        assert forbidden not in source, path
        assert "sizer_champ.Add" in source
        compile(source, str(path), "exec")
