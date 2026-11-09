# -*- coding: utf-8 -*-
"""TW-UI-01 phase 3 : garde-fous du cycle de vie Windows."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_fermeture_pendant_un_envoi_est_expliquee_et_non_reentrante():
    src = (ROOT / "teamworks" / "Utils" / "UTILS_MailingSession.py").read_text(
        encoding="utf-8"
    )
    assert "event.CanVeto()" in src
    assert "event.Veto()" in src
    assert "Fermer cette fenetre ne l'annule pas" in src
    assert "wx.CallAfter(_demarrer)" in src
    assert "dialogue.SetEscapeId(wx.ID_NONE)" in src
    assert "worker.join()" in src


def test_banc_reel_win32_qualifie_fermeture_et_retour_en_fenetre():
    script = (ROOT / "tools" / "smoke_tw_ui_01_windows_lifecycle.py").read_text(
        encoding="utf-8"
    )
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    assert "smoke_tw_ui_01_windows_lifecycle.py" in ci
    assert "dlg.Close()" in script
    assert "assert dlg.IsModal()" in script
    assert "threading.enumerate()" in script
    assert "GetWindowPlacement" in script
    assert "GetForegroundWindow" in script
    assert "cadre.Iconize(True)" in script
    assert "TW_UI01_CLOSE_PASS" in script
