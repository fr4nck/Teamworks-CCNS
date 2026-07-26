#!/usr/bin/env python3
"""Extend Teamworks smoke mode to activate each main toolbook page."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Teamworks.py"

OLD = '''        if os.environ.get("TEAMWORKS_SMOKE_MODE") == "main-window":
            print("TEAMWORKS_SMOKE_MAIN_WINDOW_READY", flush=True)
            wx.CallLater(5000, self.ExitMainLoop)
            return True
'''

BROKEN = '''        if os.environ.get("TEAMWORKS_SMOKE_MODE") == "main-window":
            print("TEAMWORKS_SMOKE_MAIN_WINDOW_READY", flush=True)

            def smoke_activate_page(index):
                frame.toolbook.SetSelection(index)
                frame.toolbook.MAJ_panel(index)
                print(f"TEAMWORKS_SMOKE_TAB_READY:{index}", flush=True)

            for delay, index in enumerate(range(frame.toolbook.GetPageCount()), start=1):
                wx.CallLater(delay * 1000, smoke_activate_page, index)
            wx.CallLater((frame.toolbook.GetPageCount() + 2) * 1000, self.ExitMainLoop)
            return True
'''

NEW = '''        if os.environ.get("TEAMWORKS_SMOKE_MODE") == "main-window":
            print("TEAMWORKS_SMOKE_MAIN_WINDOW_READY", flush=True)

            def smoke_activate_page(index):
                frame.toolBook.SetSelection(index)
                frame.toolBook.MAJ_panel(index)
                print(f"TEAMWORKS_SMOKE_TAB_READY:{index}", flush=True)

            for delay, index in enumerate(range(frame.toolBook.GetPageCount()), start=1):
                wx.CallLater(delay * 1000, smoke_activate_page, index)
            wx.CallLater((frame.toolBook.GetPageCount() + 2) * 1000, self.ExitMainLoop)
            return True
'''


def main() -> int:
    source = TARGET.read_text(encoding="iso-8859-15")
    if NEW in source:
        print("main tab smoke mode already present")
        return 0
    if BROKEN in source:
        TARGET.write_text(source.replace(BROKEN, NEW), encoding="iso-8859-15")
        print(f"repaired {TARGET.relative_to(ROOT)}")
        return 0
    count = source.count(OLD)
    if count != 1:
        raise SystemExit(f"expected exactly one main-window smoke block, found {count}")
    TARGET.write_text(source.replace(OLD, NEW), encoding="iso-8859-15")
    print(f"updated {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
