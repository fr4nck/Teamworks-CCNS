#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Adaptateur 0.9.1f de la page Généralités.

La page historique reste la source de la logique métier. Cette sous-classe
retire les hypothèses françaises bloquantes, rend l'adresse directement
saisissable et garantit que toutes les sections restent accessibles quelle que
soit la taille de la fenêtre ou l'échelle de l'interface.
"""

import wx

from Ctrl import CTRL_Page_generalites as LEGACY
from Utils import UTILS_Generalites_international as INTERNATIONAL
from Utils import UTILS_Interface
from Utils import UTILS_Responsive
from Utils import UTILS_Styles
from Utils.UTILS_Traduction import _


class Panel_general(LEGACY.Panel_general):
    def __init__(self, *args, **kwargs):
        self._responsive_columns = None
        self._scroll_host = None
        self._responsive_layout_busy = False
        LEGACY.Panel_general.__init__(self, *args, **kwargs)

        # La page historique comprimait les sections dans la hauteur du notebook.
        # En cas de petite fenêtre, zoom élevé ou Snap Windows, l'adresse pouvait
        # se retrouver hors de la zone réellement utilisable sans barre de
        # défilement. On conserve les contrôles métier mais on les héberge dans
        # une zone verticale scrollable.
        self._installer_zone_defilante()
        self._appliquer_mode_pays_naissance()
        self._configurer_cp_residence_libre()
        self.text_cp.Bind(wx.EVT_TEXT, self._on_cp_residence_libre)
        self.Bind(wx.EVT_SIZE, self._on_responsive_size)

        # Pas de CallAfter ici : le premier affichage doit être stabilisé avant
        # que l'utilisateur ne voie la fenêtre se construire par morceaux.
        self.Layout()
        self._appliquer_layout_responsive(force=True)

    def _sections(self):
        return (
            self.section_identite,
            self.section_situation,
            self.section_adresse,
            self.section_coords,
            self.section_memo,
        )

    def _nom_pays_naissance(self):
        pays = self.Recherche_Pays(IDpays=self.IDpays_naiss)
        return pays[2] if pays else "France"

    def _naissance_en_france(self):
        return INTERNATIONAL.est_france(self._nom_pays_naissance())

    def _configurer_masque_cp_naissance(self, france):
        """Le CP de naissance est français ou libre/facultatif à l'étranger."""
        try:
            valeur = self.text_cp_naiss.GetValue().strip()
            self.text_cp_naiss.SetCtrlParameters(mask="#####" if france else "")
            if valeur:
                self.text_cp_naiss.SetValue(valeur)
        except Exception:
            # Les anciennes variantes de wx.lib.masked ne proposent pas toutes
            # le même setter. La ville libre reste dans tous les cas non bloquante.
            pass

    def _configurer_cp_residence_libre(self):
        """Ne bloque jamais une adresse de résidence sur le masque français.

        Le bouton « Rechercher » reste disponible pour l'assistance française,
        mais la saisie directe doit accepter un code postal étranger ou atypique.
        """
        try:
            valeur = self.text_cp.GetValue().strip()
            self.text_cp.SetCtrlParameters(mask="")
            if valeur:
                self.text_cp.SetValue(valeur)
        except Exception:
            # Le comportement non bloquant est également assuré par les
            # gestionnaires de ville surchargés ci-dessous.
            pass
        self.text_cp.SetToolTip(
            wx.ToolTip(_(u"Saisissez librement le code postal ; utilisez Rechercher pour l'assistance française"))
        )
        self.text_ville.SetToolTip(
            wx.ToolTip(_(u"Saisissez librement la ville ; utilisez Rechercher pour l'assistance française"))
        )

    def _appliquer_mode_pays_naissance(self):
        france = self._naissance_en_france()
        # L'autocomplétion historique reste utilisable pour la naissance en
        # France. La résidence est volontairement libre et non bloquante.
        self.autoComplete = True
        self._configurer_masque_cp_naissance(france)
        if france:
            self.text_cp_naiss.SetToolTip(
                wx.ToolTip(_(u"Saisissez le code postal français"))
            )
            self.text_ville_naiss.SetToolTip(
                wx.ToolTip(_(u"Choisissez une ville dans la liste proposée"))
            )
        else:
            self.text_cp_naiss.SetToolTip(
                wx.ToolTip(_(u"Code postal de naissance facultatif"))
            )
            self.text_ville_naiss.SetToolTip(
                wx.ToolTip(_(u"Saisissez librement la ville de naissance"))
            )

    def _scale_percent(self):
        try:
            return max(80, min(220, int(round(UTILS_Styles.Scale(100)))))
        except Exception:
            return 100

    def _detach_window_from_sizer(self, sizer, window):
        """Retire une section de son ancien sizer avant de la réutiliser."""
        if sizer is None:
            return False
        for item in list(sizer.GetChildren()):
            if item.IsWindow() and item.GetWindow() is window:
                sizer.Detach(window)
                return True
            if item.IsSizer() and self._detach_window_from_sizer(
                item.GetSizer(), window
            ):
                return True
        return False

    def _detacher_sections_du_layout_courant(self, sizer=None):
        if sizer is None:
            if self._scroll_host is not None:
                sizer = self._scroll_host.GetSizer()
            else:
                sizer = self.GetSizer()
        if sizer is None:
            return
        for section in self._sections():
            self._detach_window_from_sizer(sizer, section)

    def _installer_zone_defilante(self):
        """Transforme la page historique en contenu scrollable sans le dupliquer."""
        ancien_sizer = self.GetSizer()
        self._detacher_sections_du_layout_courant(ancien_sizer)

        host = wx.ScrolledWindow(
            self,
            style=wx.VSCROLL | wx.TAB_TRAVERSAL | wx.BORDER_NONE,
        )
        host.SetBackgroundColour(UTILS_Interface.GetToken("surface"))
        host.SetScrollRate(0, max(8, UTILS_Styles.Scale(12)))

        for section in self._sections():
            section.Reparent(host)

        racine = wx.BoxSizer(wx.VERTICAL)
        racine.Add(host, 1, wx.EXPAND)
        self.SetSizer(racine, deleteOld=True)
        self._scroll_host = host
        self.Layout()

    def _appliquer_layout_responsive(self, force=False):
        if self._responsive_layout_busy or self._scroll_host is None:
            return

        largeur = self._scroll_host.GetClientSize().GetWidth()
        if largeur <= 0:
            largeur = self.GetClientSize().GetWidth()
        if largeur <= 0:
            return

        colonnes = UTILS_Responsive.form_column_count(
            largeur,
            scale_percent=self._scale_percent(),
        )
        if not force and colonnes == self._responsive_columns:
            try:
                self._scroll_host.FitInside()
            except Exception:
                pass
            return

        self._responsive_layout_busy = True
        try:
            self._detacher_sections_du_layout_courant()
            section_gap = UTILS_Styles.GetLayoutSpacing("section_gap")
            page_gap = UTILS_Styles.GetLayoutSpacing("page_gap")
            sizer = wx.BoxSizer(wx.VERTICAL)

            if colonnes == 1:
                # En colonne unique, aucune section ne doit être comprimée pour
                # « tenir » artificiellement dans la fenêtre : le défilement
                # vertical est précisément là pour absorber la hauteur.
                for index, section in enumerate(self._sections()):
                    bord = wx.LEFT | wx.RIGHT | wx.TOP
                    if index == len(self._sections()) - 1:
                        bord |= wx.BOTTOM
                    sizer.Add(section, 0, wx.EXPAND | bord, page_gap)
            else:
                gauche = wx.BoxSizer(wx.VERTICAL)
                gauche.Add(
                    self.section_identite,
                    0,
                    wx.EXPAND | wx.BOTTOM,
                    section_gap,
                )
                gauche.Add(self.section_adresse, 0, wx.EXPAND)

                droite = wx.BoxSizer(wx.VERTICAL)
                droite.Add(
                    self.section_situation,
                    0,
                    wx.EXPAND | wx.BOTTOM,
                    section_gap,
                )
                droite.Add(
                    self.section_coords,
                    0,
                    wx.EXPAND | wx.BOTTOM,
                    section_gap,
                )
                droite.Add(self.section_memo, 0, wx.EXPAND)

                contenu = wx.BoxSizer(wx.HORIZONTAL)
                contenu.Add(gauche, 3, wx.EXPAND | wx.RIGHT, section_gap)
                contenu.Add(droite, 2, wx.EXPAND)
                sizer.Add(contenu, 0, wx.EXPAND | wx.ALL, page_gap)

            self._scroll_host.SetSizer(sizer, deleteOld=True)
            self._responsive_columns = colonnes
            self._scroll_host.Layout()
            self._scroll_host.FitInside()
            self.Layout()
            self._scroll_host.Refresh()
        finally:
            self._responsive_layout_busy = False

    def _on_responsive_size(self, event):
        # Recalcul synchrone : évite l'impression de construction progressive
        # et maintient le contenu cohérent pendant un Snap/resize Windows.
        self._appliquer_layout_responsive()
        event.Skip()

    def SetPaysNaiss(self, IDpays):
        LEGACY.Panel_general.SetPaysNaiss(self, IDpays)
        self._appliquer_mode_pays_naissance()
        self.SetEtatNumSecu()

    def Code_KillFocus1(self, event):
        if not self._naissance_en_france():
            self.MAJ_barre_problemes()
            self.MaJ_DateNaiss_Fiche()
            event.Skip()
            return
        return LEGACY.Panel_general.Code_KillFocus1(self, event)

    def Ville_KillFocus1(self, event):
        if not self._naissance_en_france():
            self.MAJ_barre_problemes()
            self.MaJ_DateNaiss_Fiche()
            event.Skip()
            return
        return LEGACY.Panel_general.Ville_KillFocus1(self, event)

    def VilleText1(self, event):
        if not self._naissance_en_france():
            self.MaJ_DateNaiss_Fiche()
            event.Skip()
            return
        return LEGACY.Panel_general.VilleText1(self, event)

    # Résidence -----------------------------------------------------------
    # La base locale de villes n'est qu'une aide. La saisie d'une adresse ne
    # doit jamais déclencher une boîte bloquante ni remplacer le texte saisi.
    def Code_KillFocus2(self, event):
        self.MAJ_barre_problemes()
        self.MaJ_Adresse_Fiche()
        self.SetInfobulleVille(self.text_cp, "cp")
        event.Skip()

    def Ville_KillFocus2(self, event):
        self.MAJ_barre_problemes()
        self.MaJ_Adresse_Fiche()
        self.SetInfobulleVille(self.text_ville, "ville")
        self.SetInfobulleVille(self.text_cp, "cp")
        event.Skip()

    def VilleText2(self, event):
        self.MaJ_Adresse_Fiche()
        event.Skip()

    def VilleChar2(self, event):
        event.Skip()

    def SetEtatNumSecu(self):
        pays = self._nom_pays_naissance()
        validation, message = ValideNumSecu(
            self.text_numsecu.GetValue(),
            self.combo_box_civilite.GetStringSelection(),
            self.text_date_naiss.GetValue(),
            self.text_cp_naiss.GetValue(),
            pays_naissance=pays,
        )
        if validation is False:
            self.ctrl_etat_numsecu.SetLabel(_(u"À vérifier"))
            self.ctrl_etat_numsecu.SetForegroundColour(
                UTILS_Interface.GetToken("danger")
            )
            if self.remplissageEnCours is False:
                wx.MessageBox(message, _(u"Numéro de sécurité sociale erroné"))
        elif validation is None:
            self.ctrl_etat_numsecu.SetLabel(_(u"Non renseigné"))
            self.ctrl_etat_numsecu.SetForegroundColour(
                UTILS_Interface.GetToken("on_surface_variant")
            )
        else:
            self.ctrl_etat_numsecu.SetLabel(_(u"Valide"))
            self.ctrl_etat_numsecu.SetForegroundColour(
                UTILS_Interface.GetToken("success")
            )
        self.grid_sizer_identite.Layout()

    def Importation(self):
        LEGACY.Panel_general.Importation(self)
        self._appliquer_mode_pays_naissance()
        self._configurer_cp_residence_libre()

    def _on_cp_residence_libre(self, event):
        self.MaJ_Adresse_Fiche()
        event.Skip()


def ValideNumSecu(
    texte,
    civilite,
    date_naiss,
    dep_naiss,
    pays_naissance="France",
):
    """Validation historique avec gestion explicite des naissances étrangères."""
    texteSansEsp = "".join(lettre for lettre in texte if lettre != " ")
    if not texteSansEsp:
        return None, ""
    if len(texteSansEsp) != 15:
        if len(texteSansEsp) < 15:
            return False, _(
                u"Il manque %d chiffre(s) au numéro de sécurité sociale que vous venez de saisir. Veuillez le vérifier."
            ) % (15 - len(texteSansEsp))
        return False, _(u"Le numéro de sécurité sociale n'est pas valide.")

    if civilite == "Mr" and texteSansEsp[0] != "1":
        return False, _(
            u"Le numéro de sécurité sociale ne correspond pas à la civilité de la personne (le premier chiffre devrait être 1)."
        )
    if civilite in ("Melle", "Mme") and texteSansEsp[0] != "2":
        return False, _(
            u"Le numéro de sécurité sociale ne correspond pas à la civilité de la personne (le premier chiffre devrait être 2)."
        )

    if date_naiss != "  /  /    ":
        mois = date_naiss[3:5]
        annee = date_naiss[8:10]
        if annee != texteSansEsp[1:3] or mois != texteSansEsp[3:5]:
            return False, _(
                u"Le numéro de sécurité sociale ne correspond pas à la date de naissance de la personne."
            )

    attendu = INTERNATIONAL.departement_nir_attendu(pays_naissance, dep_naiss)
    if attendu is not None and texteSansEsp[5:7] != attendu:
        return False, _(
            u"Le numéro de sécurité sociale ne correspond pas au lieu de naissance de la personne."
        )

    try:
        cle = int(texteSansEsp[13:15])
        cle_calculee = 97 - (int(texteSansEsp[:13]) % 97)
    except ValueError:
        return False, _(u"Le numéro de sécurité sociale n'est pas valide.")
    if cle != cle_calculee:
        return False, _(
            u"La clé du numéro de sécurité sociale ne semble pas cohérente. La bonne clé devrait être %02d."
        ) % cle_calculee
    return True, ""
