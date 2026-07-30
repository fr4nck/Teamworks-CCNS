#!/usr/bin/env python3
"""Extend Teamworks smoke mode to exercise repeated main-toolbook navigation."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Teamworks.py"

OLD = '''        if os.environ.get("TEAMWORKS_SMOKE_MODE") == "main-window":
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

NEW = '''        if os.environ.get("TEAMWORKS_SMOKE_MODE") == "main-window":
            print("TEAMWORKS_SMOKE_MAIN_WINDOW_READY", flush=True)

            def smoke_activate_page(index, pass_name):
                frame.toolBook.SetSelection(index)
                frame.toolBook.MAJ_panel(index)
                print(f"TEAMWORKS_SMOKE_TAB_READY:{pass_name}:{index}", flush=True)

            page_count = frame.toolBook.GetPageCount()
            route = [("forward", index) for index in range(page_count)]
            route.extend(("backward", index) for index in reversed(range(page_count)))
            for delay, (pass_name, index) in enumerate(route, start=1):
                wx.CallLater(delay * 750, smoke_activate_page, index, pass_name)
            wx.CallLater((len(route) + 2) * 750, self.ExitMainLoop)
            return True
'''

ROUND_TRIP_INVARIANTS = (
    'route = [("forward", index) for index in range(page_count)]',
    'route.extend(("backward", index) for index in reversed(range(page_count)))',
    'TEAMWORKS_SMOKE_TAB_READY:{pass_name}:{index}',
    'frame.toolBook.MAJ_panel(index)',
)


def main() -> int:
    source = TARGET.read_text(encoding="utf-8")
    if all(invariant in source for invariant in ROUND_TRIP_INVARIANTS):
        print("round-trip main tab smoke mode already present")
        return 0
    count = source.count(OLD)
    if count != 1:
        raise SystemExit(f"expected exactly one single-pass tabs smoke block, found {count}")
    TARGET.write_text(source.replace(OLD, NEW), encoding="utf-8")
    print(f"updated {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
