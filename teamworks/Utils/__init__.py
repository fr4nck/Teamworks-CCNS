# -*- coding: utf-8 -*-
"""Chargements ciblés des utilitaires historiques nécessitant un patch runtime."""

import importlib


def __getattr__(name):
    if name == "UTILS_Publipostage_donnees":
        module = importlib.import_module("%s.UTILS_Publipostage_donnees" % __name__)
        rc2 = importlib.import_module("%s.UTILS_Publipostage_donnees_rc2" % __name__)
        rc2.install(module)
        globals()[name] = module
        return module
    raise AttributeError(name)
