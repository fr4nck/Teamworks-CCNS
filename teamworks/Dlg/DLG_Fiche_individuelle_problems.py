#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Calculs ciblés du bandeau des problèmes d'une fiche individuelle."""


def _format_problems(problems):
    if not problems:
        return ""

    parts = []
    for category, labels in problems.items():
        parts.append("%s (%s)" % (category, ", ".join(labels)))
    return "       ".join(parts) + "       "


def _has_current_or_future_contract(module, IDpersonne):
    """Teste le périmètre contractuel sans charger les contrats des autres personnes."""
    if not IDpersonne:
        return False

    db = module.GestionDB.DB()
    try:
        today = str(module.datetime.date.today())
        req = """
        SELECT contrats.IDpersonne
        FROM contrats
        INNER JOIN contrats_class
            ON contrats.IDclassification = contrats_class.IDclassification
        INNER JOIN contrats_types
            ON contrats.IDtype = contrats_types.IDtype
        WHERE contrats.IDpersonne=%d
          AND ((contrats.date_fin>='%s' AND contrats.date_rupture='')
               OR (contrats.date_rupture<>'' AND contrats.date_rupture>='%s'))
        LIMIT 1;
        """ % (IDpersonne, today, today)
        db.ExecuterReq(req)
        return bool(db.ResultatReq())
    finally:
        db.Close()


def install(module):
    """Évite les recalculs globaux à l'ouverture d'une fiche individuelle."""
    if getattr(module, "_SCOPED_INDIVIDUAL_PROBLEMS_INSTALLED", False):
        return module

    base_dialog = module.Dialog

    class ScopedProblemsDialog(base_dialog):
        def __init__(self, parent, titre=module._(u"Fiche individuelle"), IDpersonne=0):
            original_contract_search = module.FonctionsPerso.Recherche_ContratsEnCoursOuAVenir
            try:
                has_contract = _has_current_or_future_contract(module, IDpersonne)
                module.FonctionsPerso.Recherche_ContratsEnCoursOuAVenir = (
                    lambda: [IDpersonne] if has_contract else []
                )
                super(ScopedProblemsDialog, self).__init__(
                    parent, titre=titre, IDpersonne=IDpersonne
                )
            except Exception:
                module.FonctionsPerso.Recherche_ContratsEnCoursOuAVenir = original_contract_search
                super(ScopedProblemsDialog, self).__init__(
                    parent, titre=titre, IDpersonne=IDpersonne
                )
            finally:
                module.FonctionsPerso.Recherche_ContratsEnCoursOuAVenir = original_contract_search

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
