from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_preferences_keep_actions_visible_and_do_not_live_retheme_main_frame():
    source = _source("teamworks/Dlg/DLG_Preferences.py")
    theme = _source("teamworks/Utils/UTILS_Theme.py")

    assert "wx.ScrolledWindow" in source
    assert "self.footer = wx.Panel" in source
    assert "wx.CallAfter(self._ajuster_textes)" not in source
    assert "apply_to_window(top, True)" not in source

    open_preferences = theme.split("def open_preferences(event):", 1)[1].split(
        "frame.Bind(wx.EVT_MENU", 1
    )[0]
    assert "apply_to_window(frame, True)" not in open_preferences
    assert "refresh_preferences()" in open_preferences


def test_theme_repaints_materialized_object_list_views_before_show():
    source = _source("teamworks/Utils/UTILS_Theme.py")

    assert 'hasattr(window, "GetObjects")' in source
    assert 'hasattr(window, "RefreshObjects")' in source
    assert "window.RefreshObjects(objects)" in source


def test_common_buttons_rebuild_bitmap_after_final_theme_metrics():
    button = _source("teamworks/Ctrl/CTRL_Bouton_image.py")
    theme = _source("teamworks/Utils/UTILS_Theme.py")

    assert "def RafraichirVisuel(self):" in button
    assert "self._stabiliser_rendu()" in button
    assert 'getattr(window, "RafraichirVisuel", None)' in theme
    assert "refresh_visual()" in theme
