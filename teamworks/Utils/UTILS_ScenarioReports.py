#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Protection des calculs de reports de scénarios contre les cycles."""

from functools import wraps
import threading


_etatCycleReports = threading.local()


def ProtegerReportContreCycles(fonction):
    """Interrompt une chaîne de reports lorsqu'une colonne est revisitée.

    La pile est locale au thread afin qu'un calcul de scénario ne pollue jamais un
    autre traitement. Lorsqu'un cycle est rencontré dans une branche imbriquée,
    l'erreur est propagée jusqu'au report racine, y compris lorsqu'un calcul passe
    par la colonne Total et donc par ``GetDictColonnes``.
    """

    @wraps(fonction)
    def wrapper(self, IDcategorie, IDpersonne, IDscenario):
        cle = (int(IDscenario), int(IDcategorie))
        pile = getattr(_etatCycleReports, "pile", None)
        racine = pile is None
        if racine:
            pile = []
            _etatCycleReports.pile = pile
            _etatCycleReports.cycle = False

        if cle in pile:
            _etatCycleReports.cycle = True
            return "+00:00", "ERREUR3", ""

        pile.append(cle)
        try:
            resultat = fonction(self, IDcategorie, IDpersonne, IDscenario)
            if getattr(_etatCycleReports, "cycle", False):
                return "+00:00", "ERREUR3", ""
            return resultat
        finally:
            pile.pop()
            if racine:
                if hasattr(_etatCycleReports, "pile"):
                    del _etatCycleReports.pile
                if hasattr(_etatCycleReports, "cycle"):
                    del _etatCycleReports.cycle

    return wrapper
