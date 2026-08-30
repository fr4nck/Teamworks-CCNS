#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Page contrats modernisée : cœur historique conservé et écritures critiques vérifiées."""

import wx

from Ctrl import CTRL_Page_contrats_core as CORE
from Ctrl.CTRL_Page_contrats_core import *  # Compatibilité des imports historiques.


class Panel_Contrats(CORE.Panel_Contrats):
    """Écran contrats actif avec écritures transactionnelles contrôlées."""

    def SupprimerContrat(self):
        index = self.list_ctrl_contrats.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                CORE._(u"Vous devez d'abord sélectionner un contrat à supprimer dans la liste."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        texteContrat = self.list_ctrl_contrats.GetItem(index, 3).GetText()
        txtMessage = CORE.six.text_type(
            CORE._(u"Voulez-vous vraiment supprimer ce contrat ? \n\n> ") + texteContrat
        )
        dlgConfirm = wx.MessageDialog(
            self,
            txtMessage,
            CORE._(u"Confirmation de suppression"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse != wx.ID_YES:
            return False

        IDcontrat = self.list_ctrl_contrats.GetItemData(index)
        DB = CORE.GestionDB.DB()
        placeholder = "%s" if DB.isNetwork else "?"
        try:
            # Suppression enfants -> parent, validée par une transaction unique.
            DB.cursor.execute(
                "DELETE FROM contrats_valchamps WHERE IDcontrat=%s" % placeholder,
                (IDcontrat,),
            )
            DB.cursor.execute(
                "DELETE FROM contrats WHERE IDcontrat=%s" % placeholder,
                (IDcontrat,),
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
                    u"Le contrat n'a pas pu être supprimé. Aucune suppression n'a été validée.\n\n"
                    u"Détail technique : %s"
                ) % err,
                CORE._(u"Suppression annulée"),
                wx.OK | wx.ICON_ERROR,
                parent=self,
            )
            return False
        DB.Close()

        self.list_ctrl_contrats.Remplissage()
        self.MAJ_barre_problemes()
        return True

    def _BasculerIndicateur(self, colonne, champ, libelle):
        index = self.list_ctrl_contrats.GetFirstSelected()
        if index == -1:
            dlg = wx.MessageDialog(
                self,
                CORE._(u"Vous devez d'abord sélectionner un contrat dans la liste."),
                "Information",
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        IDcontrat = self.list_ctrl_contrats.GetItemData(index)
        valeur_actuelle = self.list_ctrl_contrats.GetItem(index, colonne).GetText()
        nouvelle_valeur = "" if valeur_actuelle == "Oui" else "Oui"

        DB = CORE.GestionDB.DB()
        placeholder = "%s" if DB.isNetwork else "?"
        try:
            DB.cursor.execute(
                "UPDATE contrats SET %s=%s WHERE IDcontrat=%s" % (
                    champ,
                    placeholder,
                    placeholder,
                ),
                (nouvelle_valeur, IDcontrat),
            )
            if DB.cursor.rowcount == 0:
                raise RuntimeError(CORE._(u"Le contrat sélectionné n'existe plus."))
            DB.Commit()
        except Exception as err:
            try:
                DB.connexion.rollback()
            except Exception:
                pass
            DB.Close()
            wx.MessageBox(
                CORE._(
                    u"L'indicateur %s n'a pas pu être modifié. Aucune modification n'a été validée.\n\n"
                    u"Détail technique : %s"
                ) % (libelle, err),
                CORE._(u"Modification annulée"),
                wx.OK | wx.ICON_ERROR,
                parent=self,
            )
            return False
        DB.Close()

        # L'interface ne reflète la nouvelle valeur qu'après validation en base.
        self.list_ctrl_contrats.SetItem(index, colonne, nouvelle_valeur)
        self.MAJ_barre_problemes()
        return True

    def OnBoutonSignature(self, event):
        return self._BasculerIndicateur(4, "signature", CORE._(u"Signature"))

    def OnBoutonDue(self, event):
        return self._BasculerIndicateur(5, "due", CORE._(u"DUE"))
