from pathlib import Path


SOURCE_PATH = Path("teamworks/Ctrl/CTRL_Creation_modele_contrat_p1.py")


def test_contract_model_fields_use_phoenix_checkboxes_directly():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "self.EnableCheckBoxes(True)" in source
    assert "'phoenix' in wx.PlatformInfo" not in source
    assert '"phoenix" in wx.PlatformInfo' not in source


def test_contract_model_fields_source_is_utf8():
    data = SOURCE_PATH.read_bytes()
    data.decode("utf-8")
    assert b"iso-8859" not in data.lower()
