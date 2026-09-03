from pathlib import Path


def test_fiche_individuelle_dispose_du_module_generalites_historique():
    candidates = (
        Path("teamworks/Dlg/DLG_Fiche_individuelle.py"),
        Path("teamworks/Dlg/DLG_Fiche_individuelle_core.py"),
        Path("teamworks/Dlg/DLG_Fiche_individuelle_lazy.py"),
    )
    sources = "\n".join(path.read_text(encoding="utf-8") for path in candidates if path.exists())
    assert "CTRL_Page_generalites" in sources
