#!/usr/bin/env python3
"""Génère un PDF de planning avec le moteur d'impression réel de Teamworks."""

from __future__ import annotations

import datetime
import os
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"


def main() -> int:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(TEAMWORKS_DIR))
    os.chdir(TEAMWORKS_DIR)

    from Utils import UTILS_Impression_presences_graph

    with tempfile.TemporaryDirectory(prefix="teamworks-pdf-") as temp:
        pdf_path = Path(temp) / "planning_recette.pdf"
        date = datetime.date(2026, 7, 26)
        categories = {
            1: ("Animation sportive", None, 1, "(120, 180, 220)", 60),
        }
        groups = {
            1: (
                "Équipe éducative",
                0,
                0,
                1,
                [(1, date, None, "Élodie MARTIN")],
            ),
        }
        presences = [
            (1, 1, date, "09:00", "10:00", 1, "Séance multisports", 100, 300, 0, 0),
        ]

        UTILS_Impression_presences_graph.Impression(
            nom_doc=str(pdf_path),
            orientation="paysage",
            dictCategories=categories,
            dictGroupes=groups,
            dictLignes={},
            listePresences=presences,
            dictPresences={},
            coordLigne=(100, 400),
            hauteur_barre=15,
            ecart_lignes=5,
            mode_texte=2,
        )

        assert pdf_path.is_file()
        payload = pdf_path.read_bytes()
        assert payload.startswith(b"%PDF-")
        assert payload.rstrip().endswith(b"%%EOF")
        assert len(payload) > 1000
        assert len(re.findall(rb"/Type\s*/Page\b", payload)) >= 1
        assert b"/MediaBox" in payload

        print("TEAMWORKS_PDF_IMPRESSION_OK")
        print(f"pdf={pdf_path.name}:{len(payload)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
