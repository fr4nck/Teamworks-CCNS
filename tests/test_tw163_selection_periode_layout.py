from pathlib import Path


def test_selection_periode_horizontal_sizers_do_not_use_align_right():
    source = Path("teamworks/Dlg/DLG_Selection_periode.py").read_text(encoding="utf-8")

    assert "sizerStaticBox_moisAnnee.Add(self.label_mois, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)" in source
    assert "sizerStaticBox_moisAnnee.Add(self.label_annee, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)" in source
    assert "sizerStaticBox_dates.Add(self.label_date_debut, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)" in source
    assert "sizerStaticBox_dates.Add(self.label_date_fin, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)" in source
