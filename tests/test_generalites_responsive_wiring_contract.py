from pathlib import Path


RESPONSIVE = Path("teamworks/Utils/UTILS_Responsive.py")
ADAPTER = Path("teamworks/Ctrl/CTRL_Page_generalites_091e.py")


def test_helper_responsive_couvre_snap_et_zoom():
    namespace = {}
    exec(RESPONSIVE.read_text(encoding="utf-8"), namespace)
    columns = namespace["form_column_count"]
    assert columns(1720, 100) == 2
    assert columns(960, 100) == 1
    assert columns(1720, 200) == 1
    assert columns(1720, 220) == 1


def test_adaptateur_reste_point_unique_pour_generalites_091e():
    source = ADAPTER.read_text(encoding="utf-8")
    assert "LEGACY.Panel_general" in source
    assert "UTILS_Generalites_international" in source
