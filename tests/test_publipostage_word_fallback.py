# -*- coding: utf-8 -*-
"""Régression des balises Word restant visibles après le publipostage."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "teamworks/Utils/UTILS_Publipostage_controle.py"
spec = importlib.util.spec_from_file_location("word_merge_check_test", HELPER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeReplacement:
    def __init__(self):
        self.Text = ""
        self.cleared = False

    def ClearFormatting(self):
        self.cleared = True


class FakeFind:
    def __init__(self, document):
        self.document = document
        self.Replacement = FakeReplacement()
        self.cleared = False

    def ClearFormatting(self):
        self.cleared = True

    def Execute(self, *, Replace):
        assert Replace == 2
        assert self.Format is False
        assert self.MatchWildcards is False
        assert self.MatchWholeWord is False
        assert self.MatchCase is True
        assert self.Wrap == 0
        assert self.cleared and self.Replacement.cleared
        if self.document.allow_replace:
            self.document.text = self.document.text.replace(
                self.Text, self.Replacement.Text
            )


class FakeContent:
    def __init__(self, document):
        self.document = document

    @property
    def Text(self):
        return self.document.text

    @property
    def Find(self):
        self.document.find_calls += 1
        return FakeFind(self.document)


class FakeDocument:
    def __init__(self, text, *, allow_replace=True):
        self.text = text
        self.allow_replace = allow_replace
        self.find_calls = 0
        self.Content = FakeContent(self)


def test_cee_classification_can_be_recovered_in_a_legacy_word_document():
    document = FakeDocument("Forfait de 65 euros en tant que {CLASSIFICATION}.")
    module.verify_word_merge(document, [("CLASSIFICATION", "BAFA titulaire")])
    assert document.text == "Forfait de 65 euros en tant que BAFA titulaire."
    assert document.find_calls == 1


def test_word_fallback_does_not_repeat_a_successful_first_pass():
    document = FakeDocument("Contrat de TEST.")
    module.verify_word_merge(document, [("NOM", "TEST")])
    assert document.find_calls == 0


def test_word_fallback_replaces_empty_values_and_all_occurrences():
    document = FakeDocument("{CLASSIFICATION} / {CLASSIFICATION} : {BRUTMENS}")
    module.verify_word_merge(
        document, [("CLASSIFICATION", ""), ("BRUTMENS", "65")]
    )
    assert document.text == " /  : 65"


def test_word_fallback_never_silently_accepts_an_unresolved_registered_field():
    document = FakeDocument("En tant que {CLASSIFICATION}", allow_replace=False)
    with pytest.raises(RuntimeError, match="CLASSIFICATION"):
        module.verify_word_merge(document, [("CLASSIFICATION", "BAFA titulaire")])


def test_word_fallback_leaves_unknown_braces_untouched():
    document = FakeDocument("{AUTRE} et {CLASSIFICATION}")
    module.verify_word_merge(document, [("CLASSIFICATION", "BAFA titulaire")])
    assert document.text == "{AUTRE} et BAFA titulaire"


def test_word_and_writer_callsites_apply_exact_token_matching():
    source = (ROOT / "teamworks/Dlg/DLG_Publiposteur.py").read_text(encoding="utf-8")
    assert "UTILS_Publipostage_controle.verify_word_merge(self.doc, listeValeurs)" in source
    assert "self.Word.Selection.Delete()" in source
    assert "find.ClearFormatting()" in source
    assert "orempl.SearchWords = False" in source
