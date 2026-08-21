#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Coque moderne du calendrier Teamworks.

Le moteur historique de dessin et de sélection vit dans
``CTRL_Calendrier_tw_core``. Ce module expose la même API publique, mais
centralise désormais la palette, les métriques et la navigation dans la
charte graphique Teamworks.
"""

import datetime
import sys
import wx

from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Calendrier_tw_core as CORE
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


# Le moteur métier/dessin est conservé tel quel.
Calendrier = CORE.Calendrier


class CTRL_Annee(wx.SpinCtrl):
    def __init__(self, parent):
        wx.SpinCtrl.__init__(self, parent, -1, min=1950, max=2999)
        self.parent = parent
        self.SetMinSize((UTILS_Styles.Scale(78), -1))
        self.SetToolTip(wx.ToolTip(_(u"Sélectionnez une année")))
        self.SetAnnee(datetime.date.today().year)

    def SetAnnee(self, annee=None):
        self.SetValue(annee)

    def GetAnnee(self):
        return self.GetValue()


class Panel(wx.Panel):
    """Calendrier navigable utilisant exclusivement le design system.

    ``callbacksenddates`` reste le contrat privilégié pour les dialogues qui
    consomment une sélection de dates. ``MAJselectionDates`` mémorise aussi la
    sélection pour préserver l'API historique sans connaître le parent métier.
    """

    def __init__(
        self,
        parent,
        ID=-1,
        afficheBoutonAnnuel=True,
        afficheAujourdhui=True,
        bordHaut=0,
        bordBas=0,
        bordLateral=0,
        callbacksenddates=None,
    ):
        wx.Panel.__init__(self, parent, ID, name="panel_calendrier", style=wx.TAB_TRAVERSAL)
        self.afficheBoutonAnnuel = afficheBoutonAnnuel
        self._selection_dates = []
        self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_lowest"))

        self.calendrier = Calendrier(
            self,
            -1,
            callbacksenddates=callbacksenddates,
        )
        self.calendrier.SetBackgroundColour(
            UTILS_Interface.GetToken("surface_container_lowest")
        )
        self._appliquer_palette()

        self.listeMois = [
            _(u"Janvier"), _(u"Février"), _(u"Mars"), _(u"Avril"),
            _(u"Mai"), _(u"Juin"), _(u"Juillet"), _(u"Août"),
            _(u"Septembre"), _(u"Octobre"), _(u"Novembre"), _(u"Décembre"),
        ]
        if "linux" in sys.platform:
            self.listeMois = [
                _(u"Janv."), _(u"Fév."), _(u"Mars"), _(u"Avril"),
                _(u"Mai"), _(u"Juin"), _(u"Juil."), _(u"Août"),
                _(u"Sept."), _(u"Oct."), _(u"Nov."), _(u"Déc."),
            ]

        self.combo_mois = wx.ComboBox(
            self,
            -1,
            "",
            choices=self.listeMois,
            style=wx.CB_READONLY,
        )
        self.combo_mois.SetMinSize((UTILS_Styles.Scale(118), -1))

        self.ctrl_annee = CTRL_Annee(self)
        self.spin = wx.SpinButton(self, -1, style=wx.SP_HORIZONTAL)
        taille_controle = UTILS_Styles.GetControlMetric("input_min_height")
        self.spin.SetMinSize((UTILS_Styles.Scale(42), taille_controle))
        self.spin.SetRange(-1, 1)

        self.bouton_CalendrierAnnuel = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Vue annuelle"),
        )
        self.bouton_CalendrierAnnuel.SetToolTip(
            wx.ToolTip(_(u"Afficher le calendrier annuel"))
        )

        date_jour = datetime.datetime.today()
        self.combo_mois.SetSelection(date_jour.month - 1)
        self.ctrl_annee.SetAnnee(date_jour.year)
        self.MAJPeriodeCalendrier()

        self._do_layout(bordHaut, bordBas, bordLateral)

        self.Bind(wx.EVT_SPIN, self.OnSpin, self.spin)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuel, self.bouton_CalendrierAnnuel)
        self.Bind(wx.EVT_COMBOBOX, self.OnComboMois, self.combo_mois)
        self.ctrl_annee.Bind(wx.EVT_SPINCTRL, self.OnCtrlAnnee)

        self.bouton_CalendrierAnnuel.Show(bool(self.afficheBoutonAnnuel))

        if afficheAujourdhui:
            self.calendrier.SelectJours([datetime.date.today()])

    def _appliquer_palette(self):
        """Mappe tous les états visuels sur les cinq familles de la charte."""
        couleurs = {
            "couleurFond": "surface_container_lowest",
            "couleurNormal": "surface_container_lowest",
            "couleurWE": "surface_container_low",
            "couleurSelect": "primary_container",
            "couleurSurvol": "primary",
            "couleurFontJours": "on_surface",
            "couleurVacances": "warning",
            "couleurFontJoursAvecPresents": "primary",
            "couleurFerie": "surface_container_high",
        }
        for attribut, token in couleurs.items():
            setattr(self.calendrier, attribut, UTILS_Interface.GetToken(token))
        self.calendrier.MAJAffichage()

    def _do_layout(self, bordHaut, bordBas, bordLateral):
        gap = UTILS_Styles.GetLayoutSpacing("control_gap")
        padding_horizontal = (
            max(
                UTILS_Styles.GetLayoutSpacing("content_padding"),
                UTILS_Styles.Scale(bordLateral),
            )
            if bordLateral
            else UTILS_Styles.GetLayoutSpacing("content_padding")
        )
        top = max(0, UTILS_Styles.Scale(bordHaut))
        bottom = max(0, UTILS_Styles.Scale(bordBas))

        navigation = wx.WrapSizer(wx.HORIZONTAL)
        navigation.Add(
            self.bouton_CalendrierAnnuel,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM,
            gap,
        )
        navigation.Add(
            self.combo_mois,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM,
            gap,
        )
        navigation.Add(
            self.ctrl_annee,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM,
            gap,
        )
        navigation.Add(
            self.spin,
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM,
            gap,
        )

        sizer = wx.BoxSizer(wx.VERTICAL)
        if top:
            sizer.AddSpacer(top)
        sizer.Add(
            navigation,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT,
            padding_horizontal,
        )
        sizer.Add(
            self.calendrier,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
            padding_horizontal,
        )
        if bottom:
            sizer.AddSpacer(bottom)
        self.SetSizer(sizer)

    def SetSelectionDates(self, listeDates):
        self._selection_dates = list(listeDates)

    def GetSelectionDates(self):
        return list(self._selection_dates)

    def MAJselectionDates(self, listeDates):
        """Réception générique des dates envoyées par le moteur calendrier."""
        self.SetSelectionDates(listeDates)

    def OnSpin(self, event):
        delta = event.GetPosition()
        if self.combo_mois.IsEnabled():
            mois = self.combo_mois.GetSelection() + 1 + delta
            annee = self.ctrl_annee.GetAnnee()
            if mois == 0:
                mois = 12
                annee -= 1
            elif mois == 13:
                mois = 1
                annee += 1
            self.combo_mois.SetSelection(mois - 1)
            self.ctrl_annee.SetAnnee(annee)
        else:
            self.ctrl_annee.SetAnnee(self.ctrl_annee.GetAnnee() + delta)
        self.spin.SetValue(0)
        self.MAJPeriodeCalendrier()

    def OnBoutonAnnuel(self, event):
        if self.calendrier.GetTypeCalendrier() == "mensuel":
            self.calendrier.SetTypeCalendrier("annuel")
            self.combo_mois.Enable(False)
            self.bouton_CalendrierAnnuel.SetTexte(_(u"Vue mensuelle"))
            self.bouton_CalendrierAnnuel.SetToolTip(
                wx.ToolTip(_(u"Afficher le calendrier mensuel"))
            )
        else:
            self.calendrier.SetTypeCalendrier("mensuel")
            self.combo_mois.Enable(True)
            self.bouton_CalendrierAnnuel.SetTexte(_(u"Vue annuelle"))
            self.bouton_CalendrierAnnuel.SetToolTip(
                wx.ToolTip(_(u"Afficher le calendrier annuel"))
            )
        self.Layout()

    def MAJPeriodeCalendrier(self):
        mois = self.combo_mois.GetSelection() + 1
        annee = int(self.ctrl_annee.GetValue())
        self.calendrier.SetMoisAnneeCalendrier(mois, annee)

    def OnComboMois(self, event):
        self.MAJPeriodeCalendrier()

    def OnCtrlAnnee(self, event):
        self.MAJPeriodeCalendrier()

    def MAJpanel(self):
        self._appliquer_palette()
        self.calendrier.MAJpanel()

    def MAJcontrolesNavigation(self, mois, annee):
        self.combo_mois.SetSelection(mois - 1)
        self.ctrl_annee.SetAnnee(annee)


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.panel = Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        UTILS_Styles.ApplyWindowProfile(self, "standard")


def main():
    app = wx.App()
    frame = TestFrame(None, title=_(u"Calendrier"))
    frame.Show(True)
    frame.Centre()
    app.MainLoop()


if __name__ == "__main__":
    main()
