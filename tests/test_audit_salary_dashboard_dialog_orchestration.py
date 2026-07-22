from pathlib import Path


def test_boutons_tableau_de_bord_utilisent_les_filtres_existants_sans_reconstruction():
    source = Path("teamworks/Dlg/DLG_CCNS_audit_list.py").read_text(encoding="utf-8")
    assert 'wx.Button(self, -1, "Voir les non conformes")' in source
    assert 'wx.Button(self, -1, "Voir les non évaluables")' in source
    assert 'self._apply_salary_status_filter("Non conforme")' in source
    assert 'self._apply_salary_status_filter("Non évaluable")' in source
    helper = source[source.index("    def _apply_salary_status_filter"):source.index("    def OnShowNonCompliant")]
    assert "self.ctrl_salary_status.SetValue(label)" in helper
    assert "self.OnApplyFilters(None)" in helper
    assert "audit_contracts" not in helper
    assert "salary_dashboard_from_audit_rows(self.filtered_rows)" in source
