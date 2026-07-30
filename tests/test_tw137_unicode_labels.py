# -*- coding: utf-8 -*-

from Utils import UTILS_Traduction


def test_calendar_month_names_with_replacement_character_are_repaired():
    assert UTILS_Traduction._("F�vrier") == "Février"
    assert UTILS_Traduction._("Ao�t") == "Août"
    assert UTILS_Traduction._("D�cembre") == "Décembre"


def test_abbreviated_month_names_are_repaired():
    assert UTILS_Traduction._("F�v.") == "Fév."
    assert UTILS_Traduction._("D�c.") == "Déc."


def test_recoverable_utf8_mojibake_is_repaired():
    assert UTILS_Traduction.CorrigeMojibake("CrÃ©ation") == "Création"
    assert UTILS_Traduction.CorrigeMojibake("AoÃ»t") == "Août"
    assert UTILS_Traduction.CorrigeMojibake("cÅ“ur") == "cœur"


def test_non_string_values_are_preserved():
    marker = object()
    assert UTILS_Traduction.CorrigeMojibake(marker) is marker
