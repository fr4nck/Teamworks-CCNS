from __future__ import annotations

from pathlib import Path
import os
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
if str(TEAMWORKS) not in sys.path:
    sys.path.insert(0, str(TEAMWORKS))

from Utils import UTILS_Blackbox  # noqa: E402


def test_blackbox_keeps_only_technical_components() -> None:
    UTILS_Blackbox.ViderChronologie()
    UTILS_Blackbox.Tracer("MENU", "menu:menu_parametrage", code=100)
    UTILS_Blackbox.Tracer("DOUBLE_CLICK", "wx:Ol.OL_contrats.ListView", code=101)
    UTILS_Blackbox.Tracer("BUTTON_CLICK", "Jean Dupont montant 42.50", code=102)

    text = UTILS_Blackbox.FormaterChronologie()
    assert "menu:menu_parametrage" in text
    assert "wx:Ol.OL_contrats.ListView" in text
    assert "system:redacted" in text
    assert "Jean Dupont" not in text
    assert "42.50" not in text


def test_blackbox_ring_buffer_is_bounded() -> None:
    UTILS_Blackbox.ViderChronologie()
    for index in range(260):
        UTILS_Blackbox.Tracer("TECH_EVENT", "system:test", code=index)

    snapshot = UTILS_Blackbox.SnapshotChronologie()
    assert len(snapshot) == 200
    assert snapshot[0]["code"] == 60
    assert snapshot[-1]["code"] == 259


def test_freeze_report_contains_technical_timeline_and_no_environment_value(
    tmp_path: Path, monkeypatch
) -> None:
    marker = "TW188_SECRET_ENV_VALUE"
    monkeypatch.setenv("TW188_SECRET", marker)
    UTILS_Blackbox.ViderChronologie()
    UTILS_Blackbox.Tracer("MENU", "menu:contrats_modeles", code=200)
    UTILS_Blackbox.Tracer("WINDOW_SHOW", "wx:Dlg.DLG_Config_modeles_contrats.Dialog", code=201)

    path = UTILS_Blackbox.EcrireRapportFreeze(
        12.5,
        version="0.9-test",
        repertoire=str(tmp_path),
    )

    text = Path(path).read_text(encoding="utf-8")
    assert "rapport de gel de l'interface" in text
    assert "menu:contrats_modeles" in text
    assert "wx:Dlg.DLG_Config_modeles_contrats.Dialog" in text
    assert "Piles des threads" in text
    assert "Version application: 0.9-test" in text
    assert marker not in text
    assert "aucun montant" in text
    assert "aucune requête SQL" in text


def test_watchdog_writes_one_report_when_ui_heartbeat_stalls(tmp_path: Path) -> None:
    UTILS_Blackbox.ArreterWatchdog()
    # Laisser un éventuel watchdog précédent terminer proprement.
    time.sleep(0.03)

    UTILS_Blackbox.ViderChronologie()
    UTILS_Blackbox.DemarrerWatchdog(
        lambda: None,
        version="watchdog-test",
        seuil_secondes=0.05,
        intervalle_secondes=0.01,
        repertoire=str(tmp_path),
    )

    deadline = time.monotonic() + 2.0
    reports = []
    while time.monotonic() < deadline:
        reports = list(tmp_path.glob("freeze-*.txt"))
        if reports:
            break
        time.sleep(0.01)

    UTILS_Blackbox.ArreterWatchdog()
    assert len(reports) == 1
    text = reports[0].read_text(encoding="utf-8")
    assert "FREEZE_DETECTED" in text
    assert "watchdog-test" in text


def test_wx_event_filter_never_reads_widget_values_or_labels() -> None:
    source = (TEAMWORKS / "Utils" / "UTILS_Rapport_bugs.py").read_text(encoding="utf-8")
    start = source.index("class _BlackboxEventFilter")
    end = source.index("def Activer_boite_noire_wx", start)
    filter_source = source[start:end]

    for forbidden in ("GetValue(", "GetString(", "GetLabel(", "GetText("):
        assert forbidden not in filter_source

    assert "wx.EvtHandler.AddFilter" in source
    assert "EVT_LEFT_DCLICK" in source
    assert "EVT_WINDOW_CREATE" in source
    assert "EVT_SHOW" in source
    assert "wx.App.MainLoop = mainloop_with_blackbox" in source
