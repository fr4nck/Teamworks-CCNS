import types

import pytest

from tools.recette_windows.errors import DestructiveDialogDetected
from tools.recette_windows.guards import (
    assert_not_destructive,
    looks_destructive,
    looks_like_destructive_confirmation,
    normalize_text,
)
from tools.recette_windows.selectors import find_named


class FakeElement:
    def __init__(self, name, control_type="Pane", visible=True, enabled=True):
        self.element_info = types.SimpleNamespace(name=name, control_type=control_type)
        self._visible = visible
        self._enabled = enabled

    def window_text(self):
        return self.element_info.name

    def is_visible(self):
        return self._visible

    def is_enabled(self):
        return self._enabled


def test_normalize_text_is_accent_and_space_insensitive():
    assert normalize_text("  État   des dossiers ") == "etat des dossiers"


def test_destructive_guard_rejects_delete_confirmation():
    assert looks_destructive(["Confirmer la suppression de cette fiche ?"])
    assert looks_like_destructive_confirmation(["Confirmer la suppression de cette fiche ?"])
    with pytest.raises(DestructiveDialogDetected):
        assert_not_destructive(["Supprimer définitivement"], context="test")


def test_destructive_guard_allows_safe_options_dialog():
    texts = ["Options", "Colonnes visibles", "OK", "Annuler"]
    assert not looks_destructive(texts)
    assert not looks_like_destructive_confirmation(texts)
    assert_not_destructive(texts)


def test_delete_button_alone_is_not_mistaken_for_confirmation_dialog():
    assert looks_destructive(["Supprimer"])
    assert not looks_like_destructive_confirmation(["Fiche individuelle", "Supprimer"])


def test_find_named_prefers_visible_enabled_exact_match():
    hidden = FakeElement("Individus", visible=False)
    good = FakeElement("Individus", control_type="Button")
    assert find_named([hidden, good], " individus ") is good


def test_find_named_can_filter_control_type():
    pane = FakeElement("OL_personnes", control_type="Pane")
    list_view = FakeElement("OL_personnes", control_type="List")
    assert find_named([pane, list_view], "OL_personnes", control_types=("List",)) is list_view
