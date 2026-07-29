from pathlib import Path


def test_no_wx_imagefrombitmap_remains() -> None:
    """Empêche la réintroduction de l'ancien constructeur wxPython Classic."""
    offenders: list[str] = []

    for path in Path("teamworks").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "wx.ImageFromBitmap(" in text:
            offenders.append(str(path))

    assert offenders == [], f"wx.ImageFromBitmap reste présent dans : {offenders}"
