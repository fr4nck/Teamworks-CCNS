from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Utils" / "UTILS_Adaptations.py"


def test_phoenix_checklist_bridge_disables_legacy_checkbox_rendering():
    source = TARGET.read_text(encoding="utf-8")

    assert "def _install_native_checklist_bridge():" in source
    assert "mixin.__init__ = native_init" in source
    assert "mixin.ToggleItem = native_toggle_item" in source
    assert "mixin.IsChecked = native_is_checked" in source
    assert "self.Bind(wx.EVT_LIST_ITEM_CHECKED, on_checked)" in source
    assert "self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, on_unchecked)" in source

    # Le bridge ne doit surtout pas recréer l'ancienne colonne bitmap du mixin.
    assert "SetImageList(" not in source[source.index("def _install_native_checklist_bridge():"):source.index("def _safe_person_age")]
    assert "_teamworks_native_checkbox_bridge = True" in source


def test_checkbox_bridge_source_compiles():
    source = TARGET.read_text(encoding="utf-8")
    compile(source, str(TARGET), "exec")
