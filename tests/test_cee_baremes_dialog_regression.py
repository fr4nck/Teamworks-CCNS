from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Config_cee_baremes.py"


def test_cee_rate_dialog_buttons_belong_to_inner_panel() -> None:
    source = DIALOG.read_text(encoding="utf-8")

    # wxWidgets 3.3.x refuse qu'un sizer attaché au panel gère des boutons
    # dont le parent est le wx.Dialog. Le dialogue doit donc construire
    # explicitement les boutons avec `panel` comme parent.
    assert "CreateStdDialogButtonSizer" not in source
    assert "buttons = wx.StdDialogButtonSizer()" in source
    assert "wx.Button(panel, wx.ID_OK)" in source
    assert "wx.Button(panel, wx.ID_CANCEL)" in source
    assert "buttons.Realize()" in source
