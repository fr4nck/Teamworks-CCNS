from pathlib import Path

from scripts import audit_iconography


ROOT = Path(__file__).resolve().parents[1]


def test_iconography_audit_classifies_all_raw_button_families_as_high_priority(tmp_path):
    source = tmp_path / "sample.py"
    source.write_text(
        '\n'.join((
            'self.action = wx.Button(self, -1, "Action")',
            'self.toggle = wx.ToggleButton(self, -1, "État")',
            'self.bitmap = wx.BitmapButton(self, -1, wx.Bitmap("Images/16x16/Ajouter.png"))',
        )) + '\n',
        encoding="utf-8",
    )
    hits, files = audit_iconography.scan(str(tmp_path))
    codes = {item["code"] for item in hits}
    assert "action.raw-button" in codes
    assert "action.raw-toggle-button" in codes
    assert "action.bitmap-button" in codes
    assert "asset.fixed-raster-path" in codes
    assert "asset.direct-wx-bitmap" in codes
    assert len(files) == 1


def test_iconography_audit_reads_legacy_cp1252_sources(tmp_path):
    source = tmp_path / "legacy.py"
    source.write_bytes(
        'libellé = "Éditer"\nself.button = wx.BitmapButton(self, -1)\n'.encode("cp1252")
    )
    hits, files = audit_iconography.scan(str(tmp_path))
    assert any(item["code"] == "action.bitmap-button" for item in hits)
    assert files[0]["encoding"] == "cp1252"


def test_iconography_audit_is_non_blocking_and_scans_real_tree():
    report = audit_iconography.build_report(str(ROOT / "teamworks"))
    assert report["summary"]["files"] > 0
    assert report["summary"]["by_severity"]["high"] > 0
    assert any(
        code in report["summary"]["by_code"]
        for code in (
            "action.raw-button",
            "action.raw-toggle-button",
            "action.bitmap-button",
            "action.toolbar-bitmap",
        )
    )


def test_central_image_button_chooses_multiresolution_source_before_resize():
    source = (ROOT / "teamworks" / "Ctrl" / "CTRL_Bouton_image.py").read_text(
        encoding="utf-8"
    )
    assert "ICON_RESOURCE_SIZES" in source
    assert "taille_cible = _echelle_taille(self.tailleImage)" in source
    assert "_chemin_image_existant(self.cheminImage, max(taille_cible))" in source


def test_central_button_contract_covers_plain_actions_and_toggles():
    source = (ROOT / "teamworks" / "Ctrl" / "CTRL_Bouton_image.py").read_text(
        encoding="utf-8"
    )
    assert "class CTRL(wx.Button):" in source
    assert "class Toggle(wx.ToggleButton):" in source
    assert "_appliquer_contrat_bouton" in source
    assert 'GetControlMetric("button_min_height")' in source
    assert "BUTTON_ROLES" in source
