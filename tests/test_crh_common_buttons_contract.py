
import ast
from collections import Counter
from pathlib import Path

import pytest


ROOT = Path("teamworks/Dlg")

EXPECTED = [
    ("DLG_Organismes_connexions_rh.py",
     {"wx.ID_OK": 3, "wx.ID_CANCEL": 3, "wx.ID_CLOSE": 1, "-1": 6}, 2),
    ("DLG_Demarches_rh.py",
     {"wx.ID_OK": 1, "wx.ID_CANCEL": 1, "wx.ID_CLOSE": 2, "-1": 6}, 0),
    ("DLG_Protection_sociale_action.py",
     {"wx.ID_OK": 2, "wx.ID_CANCEL": 2}, 0),
    ("DLG_Demarches_rh_creation.py",
     {"wx.ID_OK": 1, "wx.ID_CANCEL": 1}, 0),
    ("DLG_Demarches_rh_historique.py",
     {"wx.ID_CLOSE": 1}, 0),
    ("DLG_Demarches_rh_pieces.py",
     {"wx.ID_OK": 1, "wx.ID_CANCEL": 1,
      "wx.ID_CLOSE": 1, "-1": 3}, 0),
]


@pytest.mark.parametrize("filename, expected_ids, preexisting", EXPECTED)
def test_all_crh_buttons_use_common_control(filename, expected_ids, preexisting):
    tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
    common = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if not isinstance(func.value, ast.Name):
            continue

        if func.value.id == "wx":
            assert func.attr not in (
                "Button", "BitmapButton", "ToggleButton"
            ), filename

        if func.value.id == "CTRL_Bouton_image" and func.attr == "CTRL":
            common.append(node)

    assert len(common) == sum(expected_ids.values()) + preexisting

    ids = Counter()

    for call in common:
        keywords = {keyword.arg: keyword.value for keyword in call.keywords}
        if "id" not in keywords:
            continue

        assert len(call.args) == 1
        assert "texte" in keywords

        button_id = ast.unparse(keywords["id"])
        ids[button_id] += 1

        if button_id in ("wx.ID_CANCEL", "wx.ID_CLOSE"):
            assert ast.literal_eval(keywords["role"]) == "quiet"
        elif button_id == "wx.ID_OK":
            assert ast.literal_eval(keywords["role"]) == "primary"

    assert ids == Counter(expected_ids)
