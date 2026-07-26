#!/usr/bin/env python3
"""Remove popup bindings that only existed on wxPython Classic."""

from __future__ import annotations

import argparse
import tokenize
from pathlib import Path


TARGETS = {
    Path("teamworks/Ol/OL_candidats.py"): """        if 'phoenix' not in wx.PlatformInfo and \"linux\" not in sys.platform and self.activePopup == True :\n            # Désactive la fenetre popup sous Linux\n            self.Bind(wx.EVT_MOTION, self.OnMouseMotion)\n        \n""",
    Path("teamworks/Ol/OL_candidatures.py"): """        if 'phoenix' not in wx.PlatformInfo and \"linux\" not in sys.platform and self.activePopup == True :\n            # Désactive la fenetre popup sous Linux\n            self.Bind(wx.EVT_MOTION, self.OnMouseMotion)\n        \n""",
    Path("teamworks/Ctrl/CTRL_Page_generalites.py"): """        if 'phoenix' not in wx.PlatformInfo and \"linux\" not in sys.platform :\n            # Désactive la fenetre popup sous Linux\n            self.Bind(wx.EVT_MOTION, self.OnMouseMotion)\n       \n""",
}


def read_source(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        return stream.read(), stream.encoding


def migrate(path: Path, block: str, write: bool) -> int:
    source, encoding = read_source(path)
    count = source.count(block)
    if count not in (0, 1):
        raise SystemExit(f"Unexpected match count in {path}: {count}")
    if count and write:
        path.write_text(source.replace(block, ""), encoding=encoding, newline="")
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    total = 0
    for relative_path, block in TARGETS.items():
        count = migrate(args.root / relative_path, block, args.write)
        if count:
            print(f"{relative_path}: {count}")
            total += count

    print(f"classic_popup_blocks={total}")
    if args.check and total:
        raise SystemExit(f"{total} classic popup blocks remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
