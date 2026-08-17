from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANNING_SOURCE = ROOT / "teamworks" / "Ctrl" / "CTRL_Planning.py"
PRESENCES_SOURCE = ROOT / "teamworks" / "Ctrl" / "CTRL_Page_presences.py"


def test_planning_draw_helpers_round_coordinates_for_wx43() -> None:
    source = PLANNING_SOURCE.read_text(encoding="utf-8")

    assert "def _wx_int(value):" in source
    assert "def _wx_rect(x, y, width, height):" in source
    assert "dc.DrawText(texteLigne, _wx_int(posXTxt), _wx_int(posYTxt))" in source
    assert "self.pdc.DrawText(texte, _wx_int(positionTexte), _wx_int(posY-6))" in source


def test_presence_entry_dialog_close_event_is_consumed_after_endmodal() -> None:
    source = PRESENCES_SOURCE.read_text(encoding="utf-8")
    close_handler = source.split("    def OnClose(self, event):", 1)[1].split(
        "    def Fermer(self):", 1
    )[0]

    assert "self.Fermer()" in close_handler
    assert "event.Skip()" not in close_handler
