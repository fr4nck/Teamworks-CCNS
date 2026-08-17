from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Dlg" / "DLG_Publiposteur.py"


def test_publiposteur_does_not_mix_expand_and_alignment_flags() -> None:
    source = TARGET.read_text(encoding="utf-8")

    forbidden_fragments = (
        "wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL",
        "wx.EXPAND|wx.ALIGN_CENTER_VERTICAL",
        "wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND",
        "wx.ALIGN_CENTER_VERTICAL|wx.EXPAND",
    )

    for fragment in forbidden_fragments:
        assert fragment not in source

    compile(source, str(TARGET), "exec")
