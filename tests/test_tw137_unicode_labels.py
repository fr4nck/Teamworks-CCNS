# -*- coding: utf-8 -*-

import importlib
import sys
import types
from pathlib import Path


# UTILS_Traduction dépend de modules applicatifs lourds qui ne sont pas utiles
# à ces tests unitaires. On fournit uniquement les deux dépendances requises à
# l'import afin de tester la normalisation Unicode de façon isolée.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "teamworks"))
sys.modules.setdefault("Chemins", types.SimpleNamespace())
sys.modules.setdefault("Utils.UTILS_Fichiers", types.SimpleNamespace())

UTILS_Encodage = importlib.import_module("Utils.UTILS_Encodage")
UTILS_Traduction = importlib.import_module("Utils.UTILS_Traduction")


def test_clean_calendar_month_names_are_preserved():
    assert UTILS_Traduction._("Février") == "Février"
    assert UTILS_Traduction._("Août") == "Août"
    assert UTILS_Traduction._("Décembre") == "Décembre"


def test_clean_abbreviated_month_names_are_preserved():
    assert UTILS_Traduction._("Fév.") == "Fév."
    assert UTILS_Traduction._("Déc.") == "Déc."


def test_utf8_translation_keys_are_used_directly():
    UTILS_Traduction.DICT_TRADUCTIONS = {"Création": "Creation"}
    try:
        assert UTILS_Traduction._("Création") == "Creation"
    finally:
        UTILS_Traduction.DICT_TRADUCTIONS = None


def test_legacy_language_bytes_are_decoded_only_at_import_boundary():
    assert UTILS_Encodage.DecodeTexteExterne(
        "Février".encode("iso-8859-15")
    ) == "Février"
