#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fiche individuelle modernisée : cœur historique conservé et annulation transactionnelle."""

import wx

from Dlg import DLG_Fiche_individuelle_core as CORE
from Dlg.DLG_Fiche_individuelle_core import *  # Compatibilité des imports historiques.
from Utils import UTILS_Diagnostic_performance as DiagnosticPerformance


class Notebook(wx.Notebook):
    """Notebook compatible qui diffère les six pages secondaires coûteuses.

    Généralités et Questionnaire restent chargés immédiatement car la fermeture
    historique sauvegarde ces deux pages. Les autres pages sont construites au
    premier affichage, sans changer leur ordre, leur libellé ni leur classe.
    """

    def __init__(self, parent, id=-1, IDpersonne=0):
        wx.Notebook.__init__(self, parent, id, style=wx.BK_DEFAULT)
        self.IDpersonne = IDpersonne
        self._chargement_page = False

        taille_icone = CORE._taille_echelle(18, minimum=16, maximum=26)
        il = wx.ImageList(taille_icone, taille_icone)
        self.img1 = il.Add(CORE._bitmap_onglet("Identite.png", taille_icone))
        self.img2 = il.Add(CORE._bitmap_onglet("BlocNotes.png", taille_icone))
        self.img3 = il.Add(CORE._bitmap_onglet("Document.png", taille_icone))
        self.img4 = il.Add(CORE._bitmap_onglet("Presences.png", taille_icone))
        self.img5 = il.Add(CORE._bitmap_onglet("Scenario.png", taille_icone))
        self.img6 = il.Add(CORE._bitmap_onglet("Calculatrice.png", taille_icone))
        self.img7 = il.Add(CORE._bitmap_onglet("Candidature.png", taille_icone))
        self.img8 = il.Add(CORE._bitmap_onglet("Document2.png", taille_icone))
        self.AssignImageList(il)

        self.pageGeneralites = CORE.CTRL_Page_generalites.Panel_general(
            self, -1, IDpersonne=self.IDpersonne
        )
        self.AddPage(self.pageGeneralites, CORE._(u"Généralités"))
        self.SetPageImage(0, self.img1)

        if self.IDpersonne == 0:
            self.GetGrandParent().nouvelleFiche = True
            self.pageGeneralites.Sauvegarde()
            self.IDpersonne = self.pageGeneralites.IDpersonne
        else:
            self.GetGrandParent().nouvelleFiche = False

        # Le questionnaire reste eager : CORE.Dialog.Fermer() le sauvegarde
        # systématiquement, même si l'utilisateur ne visite pas son onglet.
        self.pageQuestionnaire = CORE.CTRL_Page_questionnaire.Panel(
            self, -1, IDpersonne=self.IDpersonne
        )
        self.AddPage(self.pageQuestionnaire, CORE._(u"Questionnaire"))
        self.SetPageImage(1, self.img8)

        self._specs_lazy = {
            2: ("pageStatut", CORE._(u"Qualifications"), self.img2,
                lambda: CORE.CTRL_Page_qualifications.Panel_Statut(self, -1, IDpersonne=self.IDpersonne)),
            3: ("pageContrats", CORE._(u"Contrats"), self.img3,
                lambda: CORE.CTRL_Page_contrats.Panel_Contrats(self, -1, IDpersonne=self.IDpersonne)),
            4: ("pagePresences", CORE._(u"Présences"), self.img4,
                lambda: CORE.CTRL_Page_presences.Panel(self, IDpersonne=self.IDpersonne)),
            5: ("pageScenarios", CORE._(u"Scénarios"), self.img5,
                lambda: CORE.CTRL_Page_scenarios.Panel(self, IDpersonne=self.IDpersonne)),
            6: ("pageFrais", CORE._(u"Frais"), self.img6,
                lambda: CORE.CTRL_Page_frais.Panel(self, IDpersonne=self.IDpersonne)),
            7: ("pageCandidatures", CORE._(u"Recrutement"), self.img7,
                lambda: CORE.CTRL_Page_candidatures.Panel(self, IDpersonne=self.IDpersonne)),
        }
        self._pages_lazy = {}
        for index in range(2, 8):
            attr, label, image, factory = self._specs_lazy[index]
            placeholder = wx.Panel(self, -1)
            setattr(self, attr, None)
            self._pages_lazy[index] = placeholder
            self.AddPage(placeholder, label)
            self.SetPageImage(index, image)

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def _charger_page(self, index):
        if index not in self._pages_lazy:
            return self.GetPage(index)

        attr, label, image, factory = self._specs_lazy[index]
        placeholder = self._pages_lazy.pop(index)
        with DiagnosticPerformance.mesurer_action(
            "wx.personnes.fiche.onglet.chargement",
            {"index": index, "onglet": label},
        ):
            page = factory()
            self.RemovePage(index)
            self.InsertPage(index, page, label, select=True)
            self.SetPageImage(index, image)
            setattr(self, attr, page)
            placeholder.Destroy()
        return page

    def AfficheAutresPages(self, etat=True):
        """Conserve le comportement historique des pages d'une nouvelle fiche."""
        if etat and self.GetPageCount() <= 1:
            self.AddPage(self.pageQuestionnaire, CORE._(u"Questionnaire"))
            self.SetPageImage(1, self.img8)
            for index in range(2, 8):
                attr, label, image, factory = self._specs_lazy[index]
                page = getattr(self, attr)
                if page is None:
                    page = self._pages_lazy.get(index)
                    if page is None:
                        page = wx.Panel(self, -1)
                        self._pages_lazy[index] = page
                self.AddPage(page, label)
                self.SetPageImage(self.GetPageCount() - 1, image)
        elif not etat and self.GetPageCount() > 1:
            while self.GetPageCount() > 1:
                self.RemovePage(self.GetPageCount() - 1)

    def OnPageChanged(self, event):
        if self._chargement_page:
            event.Skip()
            return

        oldPage = event.GetOldSelection()
        newPage = event.GetSelection()
        action = DiagnosticPerformance.demarrer_action(
            "wx.personnes.fiche.onglet.changement",
            {"ancien": oldPage, "nouveau": newPage},
        )
        try:
            if oldPage == 0:
                self.GetGrandParent().AnnulationImpossible = True
                self.GetGrandParent().bitmap_button_annuler.Enable(False)
                self.pageGeneralites.Sauvegarde()

            if newPage != wx.NOT_FOUND:
                self._chargement_page = True
                try:
                    page = self._charger_page(newPage)
                finally:
                    self._chargement_page = False
                page.Refresh()
        finally:
            DiagnosticPerformance.terminer_action(action)
        event.Skip()


class Dialog(CORE.Dialog):
    """Dialogue actif avec chargements mesurés et nettoyage atomique."""

    def __init__(self, *args, **kwargs):
        DiagnosticPerformance.installer_instrumentation_sql(CORE.GestionDB)
        action = DiagnosticPerformance.demarrer_action("wx.personnes.fiche.ouverture")
        notebook_original = CORE.Notebook
        CORE.Notebook = Notebook
        try:
            super(Dialog, self).__init__(*args, **kwargs)
        finally:
            CORE.Notebook = notebook_original
            DiagnosticPerformance.terminer_action(action)

    def Fermer(self, save=True):
        action = DiagnosticPerformance.demarrer_action(
            "wx.personnes.fiche.fermeture",
            {"save": bool(save), "IDpersonne": self.IDpersonne},
        )
        try:
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
        finally:
            DiagnosticPerformance.terminer_action(action)


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None, IDpersonne=1)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
