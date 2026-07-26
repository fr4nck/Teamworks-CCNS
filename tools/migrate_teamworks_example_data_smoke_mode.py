#!/usr/bin/env python3
"""Extend the GUI smoke mode to open an isolated copy of the bundled example."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Teamworks.py"

OLD = '''        if os.environ.get("TEAMWORKS_SMOKE_MODE") == "main-window":
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

NEW = '''        if os.environ.get("TEAMWORKS_SMOKE_MODE") == "main-window":
            print("TEAMWORKS_SMOKE_MAIN_WINDOW_READY", flush=True)

            for suffix in ("TDATA", "TDOCUMENTS", "TPHOTOS"):
                source = Chemins.GetStaticPath(f"Exemples/Exemple_{suffix}.dat")
                destination = UTILS_Fichiers.GetRepData(f"Exemple_{suffix}.dat")
                with open(source, "rb") as source_file, open(destination, "wb") as destination_file:
                    destination_file.write(source_file.read())

            opened = frame.OuvrirFichier("Exemple")
            if opened is False or frame.userConfig.get("nomFichier") != "Exemple":
                raise RuntimeError("unable to open bundled example data")
            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)

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


def main() -> int:
    source = TARGET.read_text(encoding="iso-8859-15")
    if NEW in source:
        print("example-data smoke mode already present")
        return 0
    count = source.count(OLD)
    if count != 1:
        raise SystemExit(f"expected exactly one tabs smoke block, found {count}")
    TARGET.write_text(source.replace(OLD, NEW), encoding="iso-8859-15")
    print(f"updated {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
