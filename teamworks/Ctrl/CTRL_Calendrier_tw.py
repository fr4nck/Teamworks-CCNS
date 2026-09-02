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

import GestionDB
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Calendrier_tw_core as CORE
from teamworks.CcnsCore.calendar_hr import build_birthdays_index, format_birthday_names
from Utils import UTILS_Interface
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


class CalendrierRh(CORE.Calendrier):
    """Calendrier historique enrichi d'informations issues du registre RH.

    Le moteur de sélection reste intact. Cette sous-classe ajoute uniquement
    une projection en lecture seule des anniversaires enregistrés dans
    ``personnes.date_naiss``.
    """

    def __init__(self, *args, **kwargs):
        self.dictAnniversaires = {}
        self._anneeAnniversaires = None
        self.couleurAnniversaire = UTILS_Interface.GetToken("primary")
        CORE.Calendrier.__init__(self, *args, **kwargs)

    def _charger_anniversaires(self, annee, force=False):
        annee = int(annee)
        if not force and self._anneeAnniversaires == annee:
            return

        rows = []
        DB = None
        try:
            DB = GestionDB.DB()
            DB.ExecuterReq(
                """
                SELECT IDpersonne, nom, prenom, date_naiss
                FROM personnes
                WHERE date_naiss IS NOT NULL AND date_naiss <> ''
                ORDER BY prenom, nom, IDpersonne;
                """
            )
            rows = DB.ResultatReq()
        except Exception:
            # Le calendrier reste utilisable même si aucune base de personnel
            # n'est ouverte (dialogues autonomes, démarrage, tests manuels).
            rows = []
        finally:
            if DB is not None:
                try:
                    DB.Close()
                except Exception:
                    pass

        self.dictAnniversaires = build_birthdays_index(rows, annee)
        self._anneeAnniversaires = annee

    def SetMoisAnneeCalendrier(self, mois=0, annee=0):
        annee_cible = int(annee or self.anneeCalendrier)
        self._charger_anniversaires(annee_cible)
        CORE.Calendrier.SetMoisAnneeCalendrier(self, mois, annee)

    def MAJpanel(self):
        self._charger_anniversaires(self.anneeCalendrier, force=True)
        CORE.Calendrier.MAJpanel(self)

    def DrawCase(self, dc, texteDate, x, y, l, h, survol=False):
        CORE.Calendrier.DrawCase(self, dc, texteDate, x, y, l, h, survol=survol)
        if texteDate not in self.dictAnniversaires:
            return

        # Petit repère visuel discret en bas à droite de la journée. Le texte
        # complet reste disponible dans la barre d'état au survol.
        couleur = self.couleurAnniversaire
        rayon = max(2, min(4, int(round(min(l, h) / 10.0))))
        centre_x = int(x + l - rayon - 4)
        centre_y = int(y + h - rayon - 4)
        dc.SetId(self.DateEnIDobjet(texteDate))
        dc.SetBrush(wx.Brush(couleur))
        dc.SetPen(wx.Pen(couleur, 1))
        dc.DrawCircle(centre_x, centre_y, rayon)

    def OnMotion(self, event):
        CORE.Calendrier.OnMotion(self, event)
        if self.caseSurvol is None:
            return

        try:
            date = self.IDobjetEnDate(self.caseSurvol)
        except Exception:
            return
        people = self.dictAnniversaires.get(date, [])
        if not people:
            return

        try:
            top = wx.GetApp().GetTopWindow()
            actuel = top.GetStatusText(0)
            marqueur = _(u" | Anniversaire : ")
            if marqueur not in actuel:
                top.SetStatusText(actuel + marqueur + format_birthday_names(people), 0)
        except Exception:
            pass


# Le moteur métier/dessin reste celui de l'historique ; l'enrichissement RH
# est volontairement contenu dans cette coque moderne.
Calendrier = CalendrierRh


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
            "couleurAnniversaire": "primary",
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
