#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Calcul ciblé du bandeau des problèmes d'une fiche individuelle."""


def _format_problems(problems):
    if not problems:
        return ""

    parts = []
    for category, labels in problems.items():
        parts.append("%s (%s)" % (category, ", ".join(labels)))
    return "       ".join(parts) + "       "


def install(module):
    """Évite un recalcul global lorsque le cache des problèmes est absent."""
    if getattr(module, "_SCOPED_INDIVIDUAL_PROBLEMS_INSTALLED", False):
        return module

    base_dialog = module.Dialog

    class ScopedProblemsDialog(base_dialog):
        def Recup_txt_pb_personne(self):
            """Lit le cache global ou calcule uniquement la personne ouverte."""
            try:
                top_window = module.wx.GetApp().GetTopWindow()
                cached = top_window.dictProblemesPersonnes
            except (AttributeError, RuntimeError):
                cached = None

            if cached is not None:
                return _format_problems(cached.get(self.IDpersonne, {}))

            _names, problems = module.FonctionsPerso.Recherche_problemes_personnes(
                listeIDpersonnes=(self.IDpersonne,)
            )
            return _format_problems(problems.get(self.IDpersonne, {}))

    ScopedProblemsDialog.__name__ = "Dialog"
    ScopedProblemsDialog.__module__ = module.__name__
    module.Dialog = ScopedProblemsDialog
    module._SCOPED_INDIVIDUAL_PROBLEMS_INSTALLED = True
    return module
