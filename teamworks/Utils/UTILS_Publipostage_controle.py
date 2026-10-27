# -*- coding: utf-8 -*-
"""Vérification des balises de publipostage Word non résolues.

Après la recherche historique basée sur Selection.Find, seules les balises
restées dans le texte principal sont recherchées une seconde fois avec
document.Content.Find, sans restriction de mise en forme.
"""


def _unresolved_fields(text, values):
    content = text or ""
    return [
        (key, value)
        for key, value in values
        if isinstance(key, str) and key and "{" + key + "}" in content
    ]


def verify_word_merge(document, values):
    """Réessaie les balises manquées puis refuse un document incomplet."""
    values = list(values or ())
    missing = _unresolved_fields(document.Content.Text, values)
    for key, value in missing:
        finder = document.Content.Find
        finder.ClearFormatting()
        finder.Replacement.ClearFormatting()
        finder.Text = "{" + key + "}"
        finder.Replacement.Text = "" if value is None else str(value)
        finder.Forward = True
        finder.Wrap = 0  # wdFindStop, plage du document entier
        finder.Format = False
        finder.MatchCase = True
        finder.MatchWildcards = False
        finder.MatchWholeWord = False
        finder.Execute(Replace=2)  # wdReplaceAll

    remaining = _unresolved_fields(document.Content.Text, values)
    if remaining:
        names = ", ".join(sorted({key for key, _value in remaining}))
        raise RuntimeError("Mots-clés de publipostage non remplacés : " + names)
