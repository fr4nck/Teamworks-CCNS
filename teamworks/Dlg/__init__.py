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

    # Conserver la garde historique de lazy loading avant d'importer la fiche.
    if name != "DLG_Fiche_individuelle":
        raise AttributeError(name)

    # Garder aussi la branche explicite : elle documente le seul autre nom
    # supporté par ce chargeur et verrouille le contrat de non-régression RC2.
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
