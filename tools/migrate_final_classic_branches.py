#!/usr/bin/env python3
"""Remove the final wxPython Classic-only branches."""

from __future__ import annotations

import argparse
import tokenize
from pathlib import Path


TARGETS = {
    Path("teamworks/Dlg/DLG_Publiposteur.py"): [
        "        if 'phoenix' not in wx.PlatformInfo:\n            wx.Yield()\n",
    ],
    Path("teamworks/Teamworks.py"): [
        "            if 'phoenix' not in wx.PlatformInfo:\n                wx.Yield()\n",
        "        if 'phoenix' not in wx.PlatformInfo:\n            wx.Yield()\n",
    ],
    Path("teamworks/Utils/UTILS_Printer.py"): [
        "        if 'phoenix' not in wx.PlatformInfo:\n            controlBar = self.GetControlBar()\n        else:\n            for ctrl in self.GetChildren():\n                if \"ControlBar\" in str(ctrl):\n                    controlBar = ctrl\n",
        "        if 'phoenix' not in wx.PlatformInfo:\n            self.MakeModal(False)\n",
    ],
}

REPLACEMENTS = {
    "        if 'phoenix' not in wx.PlatformInfo:\n            controlBar = self.GetControlBar()\n        else:\n            for ctrl in self.GetChildren():\n                if \"ControlBar\" in str(ctrl):\n                    controlBar = ctrl\n": "        for ctrl in self.GetChildren():\n            if \"ControlBar\" in str(ctrl):\n                controlBar = ctrl\n",
}


def read_source(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        return stream.read(), stream.encoding


def migrate(path: Path, blocks: list[str], write: bool) -> int:
    source, encoding = read_source(path)
    count = 0
    for block in blocks:
        matches = source.count(block)
        if matches:
            count += matches
            replacement = REPLACEMENTS.get(block, "")
            source = source.replace(block, replacement)
    if count and write:
        path.write_text(source, encoding=encoding, newline="")
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    total = 0
    for relative_path, blocks in TARGETS.items():
        count = migrate(args.root / relative_path, blocks, args.write)
        if count:
            print(f"{relative_path}: {count}")
            total += count

    print(f"classic_branches={total}")
    if args.check and total:
        raise SystemExit(f"{total} final Classic branches remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
