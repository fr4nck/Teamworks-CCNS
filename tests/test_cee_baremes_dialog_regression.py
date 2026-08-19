from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Config_cee_baremes.py"


def test_cee_rate_dialog_buttons_belong_to_inner_panel() -> None:
    source = DIALOG.read_text(encoding="utf-8")

    # wxWidgets 3.3.x refuse qu'un sizer attaché au panel gère des boutons
    # dont le parent est le wx.Dialog. Le dialogue doit donc construire
    # explicitement les boutons avec `panel` comme parent.
    assert "self.CreateStdDialogButtonSizer(" not in source
    assert "buttons = wx.StdDialogButtonSizer()" in source
    assert "wx.Button(panel, wx.ID_OK)" in source
    assert "wx.Button(panel, wx.ID_CANCEL)" in source
    assert "buttons.Realize()" in source


def test_cee_rate_dialog_reloads_rates_when_effective_date_changes() -> None:
    source = DIALOG.read_text(encoding="utf-8")

    assert "EVT_DATE_CHANGED" in source
    assert "self.date_effet.Bind(EVT_DATE_CHANGED, self.OnDateChanged)" in source
    assert "def OnDateChanged(self, event):" in source
    assert "self._load_applicable_rates()" in source
    # Un barème d'une date précédente ne doit pas rester affiché lorsque la
    # nouvelle date n'a aucune valeur applicable.
    assert 'ctrl.SetValue("")' in source
