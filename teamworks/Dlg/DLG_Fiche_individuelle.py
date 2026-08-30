#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fiche individuelle modernisée : cœur historique conservé et annulation transactionnelle."""

import wx

from Dlg import DLG_Fiche_individuelle_core as CORE
from Dlg.DLG_Fiche_individuelle_core import *  # Compatibilité des imports historiques.


class Dialog(CORE.Dialog):
    """Dialogue actif avec nettoyage atomique d'une fiche provisoire annulée."""

    def Fermer(self, save=True):
        # Tous les chemins historiques restent inchangés sauf l'annulation
        # d'une fiche neuve, qui doit être atomique.
        if save or not self.nouvelleFiche:
            return CORE.Dialog.Fermer(self, save=save)

        IDpersonne = self.IDpersonne
        DB = CORE.GestionDB.DB()
        placeholder = "%s" if DB.isNetwork else "?"
        try:
            DB.cursor.execute(
                "DELETE FROM coordonnees WHERE IDpersonne=%s" % placeholder,
                (IDpersonne,),
            )
            DB.cursor.execute(
                "DELETE FROM personnes WHERE IDpersonne=%s" % placeholder,
                (IDpersonne,),
            )
            DB.Commit()
        except Exception as err:
            try:
                DB.connexion.rollback()
            except Exception:
                pass
            DB.Close()
            wx.MessageBox(
                CORE._(
                    u"La fiche provisoire n'a pas pu être annulée. Aucune suppression n'a été validée.\n\n"
                    u"Détail technique : %s"
                ) % err,
                CORE._(u"Annulation impossible"),
                wx.OK | wx.ICON_ERROR,
                parent=self,
            )
            return False
        DB.Close()

        frm = CORE.FonctionsPerso.FrameOuverte("Personnes")
        if frm is not None:
            frm.listCtrl_personnes.MAJ(IDpersonne=IDpersonne)
            frm.panel_dossiers.tree_ctrl_problemes.MAJ_treeCtrl()
        self.EndModal(wx.ID_OK)
        return True


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, IDpersonne=1)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
