#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from cx_Freeze import Executable, setup

ROOT = Path(__file__).resolve().parent
TEAMWORKS_DIR = ROOT / "teamworks"
BUILD_DIR = ROOT / "build" / "Teamworks-CCNS"

sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(TEAMWORKS_DIR))


def read_version() -> str:
    first_line = (TEAMWORKS_DIR / "Versions.txt").read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()[0]
    match = re.search(r"Version\s+([0-9]+(?:\.[0-9]+)+)", first_line)
    if not match:
        raise RuntimeError(f"Version illisible dans Versions.txt: {first_line!r}")
    return match.group(1)


if BUILD_DIR.exists():
    shutil.rmtree(BUILD_DIR)

include_files = [
    (str(TEAMWORKS_DIR / "static"), "static"),
    (str(TEAMWORKS_DIR / "Versions.txt"), "Versions.txt"),
    (str(TEAMWORKS_DIR / "Licence.txt"), "Licence.txt"),
    (str(TEAMWORKS_DIR / "Icone.ico"), "Icone.ico"),
]

build_options = {
    "build_exe": str(BUILD_DIR),
    "include_files": include_files,
    "includes": [
        "Gadget",
        "email.mime.image",
        "idna.idnadata",
        "mailjet_rest",
        "numpy._core._methods",
        "numpy.lib.format",
    ],
    "excludes": [
        "PyQt4",
        "PyQt5",
        "gtk",
        "tkinter",
        "PIL.ImageTk",
    ],
    "optimize": 1,
    "silent_level": 1,
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="Teamworks-CCNS",
    version=read_version(),
    author="Ivan LUCAS / PMSL",
    description="Teamworks CCNS, gestion d'équipe et contrôles conventionnels",
    options={"build_exe": build_options},
    executables=[
        Executable(
            script=str(TEAMWORKS_DIR / "Teamworks.py"),
            target_name="Teamworks.exe",
            base=base,
            icon=str(TEAMWORKS_DIR / "Icone.ico"),
        )
    ],
)
