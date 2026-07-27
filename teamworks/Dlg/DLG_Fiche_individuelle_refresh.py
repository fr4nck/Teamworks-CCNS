#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rafraîchissement ciblé de la liste après fermeture d'une fiche."""


def _secondary_pages_are_unloaded(notebook):
    names = (
        "pageQuestionnaire",
        "pageStatut",
        "pageContrats",
        "pagePresences",
        "pageScenarios",
        "pageFrais",
        "pageCandidatures",
    )
    return all(getattr(notebook, name, None) is None for name in names)


def _reload_person_contacts(module, db, IDpersonne):
    """Actualise uniquement le cache des coordonnées de la personne."""
    req = """
    SELECT IDcoord, IDpersonne, categorie, texte, intitule
    FROM coordonnees WHERE IDpersonne=%d;
    """ % IDpersonne
    db.ExecuterReq(req)
    module.DICT_COORDONNEES[IDpersonne] = list(db.ResultatReq())


def _refresh_current_track(list_ctrl, IDpersonne):
    """Recharge uniquement la personne et reconstruit la projection visible."""
    try:
        from Ol import OL_personnes

        db = OL_personnes.GestionDB.DB()
        try:
            req = """
            SELECT IDpersonne, civilite, nom, nom_jfille, prenom, date_naiss,
                   cp_naiss, ville_naiss, pays_naiss, nationalite, num_secu,
                   adresse_resid, cp_resid, ville_resid, IDsituation
            FROM personnes WHERE IDpersonne=%d;
            """ % IDpersonne
            db.ExecuterReq(req)
            rows = db.ResultatReq()
            _reload_person_contacts(OL_personnes, db, IDpersonne)
        finally:
            db.Close()

        if not rows:
            return False

        replacement = OL_personnes.Track(rows[0])
        for track in list_ctrl.GetObjects():
            if getattr(track, "IDpersonne", None) == IDpersonne:
                track.__dict__.update(replacement.__dict__)
                list_ctrl.RepopulateList()
                list_ctrl.SelectObject(track, deselectOthers=True, ensureVisible=True)
                return True
    except Exception:
        return False
    return False


def install(module):
    """Installe un chemin rapide, avec repli intégral en cas de doute."""
    if getattr(module, "_TARGETED_PERSON_REFRESH_INSTALLED", False):
        return module

    base_dialog = module.Dialog

    class TargetedRefreshDialog(base_dialog):
        def Fermer(self, save=True):
            if save is False:
                if self.nouvelleFiche is True:
                    db = module.GestionDB.DB()
                    db.ReqDEL("coordonnees", "IDpersonne", self.IDpersonne)
                    db.ReqDEL("personnes", "IDpersonne", self.IDpersonne)
                    db.Close()
            else:
                if self.Verifie_validite_donnees() is True:
                    self.notebook.pageGeneralites.Sauvegarde()
                    if self.notebook.pageQuestionnaire is not None:
                        self.notebook.pageQuestionnaire.Sauvegarde()
                else:
                    return

            frame = module.FonctionsPerso.FrameOuverte("Personnes")
            if frame is not None:
                fast_path = (
                    save is True
                    and self.nouvelleFiche is False
                    and _secondary_pages_are_unloaded(self.notebook)
                    and _refresh_current_track(frame.listCtrl_personnes, self.IDpersonne)
                )
                if not fast_path:
                    frame.listCtrl_personnes.MAJ(IDpersonne=self.IDpersonne)
                frame.panel_dossiers.tree_ctrl_problemes.MAJ_treeCtrl()
            self.EndModal(module.wx.ID_OK)

    TargetedRefreshDialog.__name__ = "Dialog"
    TargetedRefreshDialog.__module__ = module.__name__
    module.Dialog = TargetedRefreshDialog
    module._TARGETED_PERSON_REFRESH_INSTALLED = True
    return module
