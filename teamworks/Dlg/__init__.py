# -*- coding: utf-8 -*-
"""Chargement ciblé des dialogues historiques."""

import importlib


def __getattr__(name):
    if name == "DLG_Publiposteur":
        module = importlib.import_module("%s.DLG_Publiposteur" % __name__)
        lifecycle = importlib.import_module("%s.DLG_Publiposteur_lifecycle" % __name__)
        lifecycle.install(module)
        globals()[name] = module
        return module

    if name == "DLG_Fiche_individuelle":
        module = importlib.import_module("%s.DLG_Fiche_individuelle" % __name__)
        lazy = importlib.import_module("%s.DLG_Fiche_individuelle_lazy" % __name__)
        problems = importlib.import_module("%s.DLG_Fiche_individuelle_problems" % __name__)
        refresh = importlib.import_module("%s.DLG_Fiche_individuelle_refresh" % __name__)
        lazy.install(module)
        problems.install(module)
        refresh.install(module)
        globals()[name] = module
        return module

    raise AttributeError(name)
