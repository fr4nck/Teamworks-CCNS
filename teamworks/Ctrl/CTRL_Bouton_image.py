#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-15 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

from pathlib import Path

from Utils import UTILS_Interface, UTILS_Styles
import wx

import PIL.Image as Image
import PIL.ImageOps as ImageOps


ICON_RESOURCE_SIZES = (16, 22, 32, 48, 80, 128)
BUTTON_ROLES = ("default", "primary", "danger", "quiet")


def PILtoWx(image):
    """Convertit une image PIL en wx.Image avec canal alpha."""
    largeur, hauteur = image.size
    imagewx = wx.Image(largeur, hauteur)
    imagewx.SetData(image.tobytes("raw", "RGB"))
    imagewx.SetAlpha(image.convert("RGBA").tobytes()[3::4])
    return imagewx


def _echelle_taille(taille):
    return tuple(UTILS_Styles.Scale(valeur) for valeur in taille)


def _echelle_marges(marges):
    if isinstance(marges, tuple):
        return tuple(UTILS_Styles.Scale(valeur, minimum=0) for valeur in marges)
    return UTILS_Styles.Scale(marges, minimum=0)


def _chemin_image_existant(chemin, taille_cible=None):
    """Renvoie la variante raster la plus adaptée à la taille réellement affichée.

    Teamworks possède encore plusieurs générations d'icônes PNG rangées dans
    des répertoires 16x16, 22x22, 32x32, 48x48, 80x80 et 128x128. Agrandir une
    source 16x16 à 40 px au zoom 200 % produit une icône floue et donne
    l'impression que l'interface ne suit pas le zoom. Quand plusieurs variantes
    d'un même fichier existent, on choisit donc la plus petite résolution au
    moins égale à la cible, ou la plus grande disponible en dernier recours.
    """
    if chemin in ("", None):
        return None

    path = Path(chemin)
    parts = list(path.parts)
    size_index = None
    for index, part in enumerate(parts):
        if part in {"%dx%d" % (size, size) for size in ICON_RESOURCE_SIZES}:
            size_index = index
            break

    # Ressource hors arborescence multi-résolution : comportement historique.
    if size_index is None:
        return path if path.is_file() else None

    candidates = []
    for size in ICON_RESOURCE_SIZES:
        variant_parts = list(parts)
        variant_parts[size_index] = "%dx%d" % (size, size)
        variant = Path(*variant_parts)
        if variant.is_file():
            candidates.append((size, variant))

    if not candidates:
        return path if path.is_file() else None

    try:
        target = max(1, int(round(float(taille_cible))))
    except (TypeError, ValueError):
        target = 0

    if target <= 0:
        return path if path.is_file() else candidates[0][1]

    larger = [(size, variant) for size, variant in candidates if size >= target]
    if larger:
        return min(larger, key=lambda item: item[0])[1]
    return max(candidates, key=lambda item: item[0])[1]


def _token_texte_bouton(role):
    """Retourne la couleur sémantique du libellé sans casser le rendu natif."""
    if role == "danger":
        return "danger"
    if role == "primary":
        return "primary"
    return "on_surface"


def _appliquer_contrat_bouton(control, texte="", role="default", icon_only=False):
    """Applique le contrat commun de densité, zoom, typo et cible cliquable."""
    if role not in BUTTON_ROLES:
        role = "default"
    control._teamworks_button_role = role
    control._teamworks_text_style = "label"
    control.SetFont(UTILS_Styles.GetFont("label"))
    control._teamworks_font_scaled = True
    control.SetForegroundColour(
        UTILS_Interface.GetToken(_token_texte_bouton(role))
    )
    control.SetInitialSize()

    best = control.GetBestSize()
    hauteur_min = UTILS_Styles.GetControlMetric("button_min_height")
    largeur_min = best.GetWidth()
    if icon_only:
        largeur_min = max(largeur_min, hauteur_min)
    control.SetMinSize((largeur_min, max(best.GetHeight(), hauteur_min)))


class CTRL(wx.Button):
    """Bouton d'action natif Teamworks consommant la charte centrale.

    Ce composant couvre les boutons texte, texte+icône et icône seule. Les
    écrans métier ne devraient pas recréer localement leurs métriques de
    hauteur, leur typographie ou leur stratégie d'icône.
    """

    def __init__(
        self,
        parent,
        id=-1,
        texte="",
        cheminImage=None,
        tailleImage=None,
        margesImage=None,
        positionImage=wx.LEFT,
        margesTexte=None,
        role="default",
    ):
        wx.Button.__init__(self, parent, id=id, label=texte)
        self.parent = parent
        self.texte = texte
        self.cheminImage = cheminImage
        self.role = role if role in BUTTON_ROLES else "default"
        taille_defaut = UTILS_Styles.ICON_SIZES["medium"]
        self.tailleImage = tailleImage or (taille_defaut, taille_defaut)
        if isinstance(self.tailleImage, tuple) is False:
            self.tailleImage = (self.tailleImage, self.tailleImage)
        marge_icone = UTILS_Styles.CONTROL_METRICS["button_icon_margin"]
        self.margesImage = margesImage if margesImage is not None else (marge_icone, 0, 0, 0)
        self.positionImage = positionImage
        self.margesTexte = margesTexte if margesTexte is not None else (0, 1)
        self._teamworks_text_style = "label"
        self.MAJ()

    def _bitmap(self):
        taille_cible = _echelle_taille(self.tailleImage)
        chemin = _chemin_image_existant(self.cheminImage, max(taille_cible))
        if chemin is None:
            return wx.NullBitmap

        try:
            img = Image.open(chemin)
        except (OSError, ValueError):
            # Une ressource décorative ne doit jamais rendre une action métier
            # inutilisable. Le libellé du bouton reste affiché.
            return wx.NullBitmap

        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = getattr(Image, "LANCZOS", Image.BICUBIC)

        img = img.resize(taille_cible, resample_filter)
        img = ImageOps.expand(img, border=_echelle_marges(self.margesImage))
        return PILtoWx(img).ConvertToBitmap()

    def MAJ(self):
        bitmap = self._bitmap()
        self.SetBitmap(bitmap, self.positionImage)
        if bitmap.IsOk():
            self.SetBitmapMargins(_echelle_marges(self.margesTexte))

        self.AppliquerTheme()
        self.SetInitialSize()

        best = self.GetBestSize()
        hauteur_min = UTILS_Styles.GetControlMetric("button_min_height")
        largeur_min = best.GetWidth()
        if bitmap.IsOk() and not self.texte:
            largeur_min = max(largeur_min, hauteur_min)
        self.SetMinSize((largeur_min, max(best.GetHeight(), hauteur_min)))

    def AppliquerTheme(self):
        """Conserve le rendu natif et applique la typographie de la charte."""
        _appliquer_contrat_bouton(
            self,
            texte=self.texte,
            role=self.role,
            icon_only=bool(self.cheminImage and not self.texte),
        )

    def SetImage(self, cheminImage=""):
        self.SetBitmap(wx.NullBitmap)
        self.cheminImage = cheminImage
        self.MAJ()

    def SetTexte(self, texte=""):
        self.texte = texte
        self.SetLabel(texte)
        self.MAJ()

    def SetRole(self, role="default"):
        self.role = role if role in BUTTON_ROLES else "default"
        self.AppliquerTheme()
        self.Refresh()


class Toggle(wx.ToggleButton):
    """Bouton à état Teamworks avec le même contrat que les actions ordinaires."""

    def __init__(self, parent, id=-1, texte="", role="default"):
        wx.ToggleButton.__init__(self, parent, id=id, label=texte)
        self.parent = parent
        self.texte = texte
        self.role = role if role in BUTTON_ROLES else "default"
        self._teamworks_text_style = "label"
        self.MAJ()

    def MAJ(self):
        self.AppliquerTheme()

    def AppliquerTheme(self):
        _appliquer_contrat_bouton(
            self,
            texte=self.texte,
            role=self.role,
            icon_only=False,
        )

    def SetTexte(self, texte=""):
        self.texte = texte
        self.SetLabel(texte)
        self.MAJ()

    def SetRole(self, role="default"):
        self.role = role if role in BUTTON_ROLES else "default"
        self.AppliquerTheme()
        self.Refresh()
