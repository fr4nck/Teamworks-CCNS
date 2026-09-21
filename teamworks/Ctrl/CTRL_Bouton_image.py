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
    """Renvoie la variante raster la plus adaptée à la taille réellement affichée."""
    if chemin in ("", None):
        return None

    path = Path(chemin)
    parts = list(path.parts)
    size_index = None
    for index, part in enumerate(parts):
        if part in {"%dx%d" % (size, size) for size in ICON_RESOURCE_SIZES}:
            size_index = index
            break

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
    if role == "danger":
        return "danger"
    if role == "primary":
        return "primary"
    return "on_surface"


def _appliquer_contrat_bouton(control, texte="", role="default", icon_only=False):
    if role not in BUTTON_ROLES:
        role = "default"
    control._teamworks_button_role = role
    control._teamworks_text_style = "label"
    control.SetFont(UTILS_Styles.GetFont("label"))
    control._teamworks_font_scaled = True
    control.SetForegroundColour(UTILS_Interface.GetToken(_token_texte_bouton(role)))
    # Recalculer le BestSize sans hériter d'une ancienne largeur maximale,
    # notamment après SetTexte().
    control.SetMaxSize((-1, -1))
    control.SetInitialSize()

    best = control.GetBestSize()
    hauteur_min = UTILS_Styles.GetControlMetric("button_min_height")
    largeur_min = best.GetWidth()
    if icon_only:
        largeur_min = max(largeur_min, hauteur_min)
    hauteur = max(best.GetHeight(), hauteur_min)
    control.SetMinSize((largeur_min, hauteur))
    # Un bouton d'action garde sa largeur naturelle. Le parent peut consommer
    # l'espace restant avec un spacer, mais ne transforme pas le bouton en barre.
    control.SetMaxSize((largeur_min, -1))


class CTRL(wx.Button):
    """Bouton d'action natif Teamworks consommant la charte centrale."""

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
        bitmap=None,
        style=0,
    ):
        wx.Button.__init__(self, parent, id=id, label=texte, style=style)
        self.parent = parent
        self.texte = texte
        self.cheminImage = cheminImage
        self.bitmapSource = bitmap
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
        if self.bitmapSource is not None:
            try:
                if self.bitmapSource.IsOk():
                    return self.bitmapSource
            except Exception:
                pass

        taille_cible = _echelle_taille(self.tailleImage)
        chemin = _chemin_image_existant(self.cheminImage, max(taille_cible))
        if chemin is None:
            return wx.NullBitmap

        try:
            img = Image.open(chemin).convert("RGBA")
        except (OSError, ValueError):
            return wx.NullBitmap

        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = getattr(Image, "LANCZOS", Image.BICUBIC)

        img = img.resize(taille_cible, resample_filter)
        img = ImageOps.expand(img, border=_echelle_marges(self.margesImage))
        return PILtoWx(img).ConvertToBitmap()

    def _stabiliser_rendu(self):
        """Force wx à considérer immédiatement bitmap, métriques et invalidation.

        Sous Windows un SetBitmap suivi de changements de police/thème pouvait
        laisser le bouton dans un état visuel intermédiaire jusqu'au rollover.
        On invalide donc le best-size et on demande le repaint dès la fin de la
        construction du contrôle, sans différer le layout via CallAfter.
        """
        try:
            if hasattr(self, "InvalidateBestSize"):
                self.InvalidateBestSize()
            self.Refresh(False)
            if self.IsShownOnScreen():
                self.Update()
        except Exception:
            pass

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
        hauteur = max(best.GetHeight(), hauteur_min)
        self.SetMinSize((largeur_min, hauteur))
        self.SetMaxSize((largeur_min, -1))
        self._stabiliser_rendu()

    def AppliquerTheme(self):
        _appliquer_contrat_bouton(
            self,
            texte=self.texte,
            role=self.role,
            icon_only=bool((self.cheminImage or self.bitmapSource is not None) and not self.texte),
        )

    def RafraichirVisuel(self):
        """Point d'entrée sûr pour le moteur de thème après zoom/apparence."""
        self.MAJ()

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
        self._stabiliser_rendu()


class Compact(wx.Button):
    """Petit bouton technique Teamworks intégré à un champ ou une grille.

    Il remplace les wx.Button/wx.BitmapButton historiques utilisés comme
    sélecteurs "..." ou déclencheurs d'icône, tout en conservant leur encombrement
    réduit. Contrairement à CTRL, il n'impose pas la hauteur d'un bouton d'action
    principal mais il consomme quand même la charte et le contrat de largeur.
    """

    def __init__(
        self,
        parent,
        id=-1,
        texte="",
        cheminImage=None,
        bitmap=None,
        size=(-1, -1),
        role="quiet",
        style=wx.BU_EXACTFIT,
    ):
        wx.Button.__init__(self, parent, id=id, label=texte, size=size, style=style)
        self.parent = parent
        self.texte = texte
        self.cheminImage = cheminImage
        self.bitmapSource = bitmap
        self.role = role if role in BUTTON_ROLES else "quiet"
        self._teamworks_text_style = "label"
        self.MAJ()

    def _bitmap(self):
        if self.bitmapSource is not None:
            try:
                if self.bitmapSource.IsOk():
                    return self.bitmapSource
            except Exception:
                pass
        if not self.cheminImage:
            return wx.NullBitmap
        chemin = _chemin_image_existant(
            self.cheminImage,
            UTILS_Styles.ICON_SIZES["small"],
        )
        if chemin is None:
            return wx.NullBitmap
        try:
            return wx.Bitmap(str(chemin), wx.BITMAP_TYPE_ANY)
        except Exception:
            return wx.NullBitmap

    def MAJ(self):
        self.SetFont(UTILS_Styles.GetFont("label"))
        self.SetForegroundColour(
            UTILS_Interface.GetToken(_token_texte_bouton(self.role))
        )
        bitmap = self._bitmap()
        if bitmap.IsOk():
            self.SetBitmap(bitmap)
            self.SetBitmapMargins((2, 0))
        self.SetInitialSize()
        best = self.GetBestSize()
        largeur = max(best.GetWidth(), 20)
        hauteur = max(best.GetHeight(), 20)
        self.SetMinSize((largeur, hauteur))
        self.SetMaxSize((largeur, hauteur))
        try:
            self.InvalidateBestSize()
            self.Refresh(False)
        except Exception:
            pass


class Toggle(wx.ToggleButton):
    """Bouton à état Teamworks avec le même contrat que les actions ordinaires."""

    def __init__(self, parent, id=-1, texte="", role="default"):
        wx.ToggleButton.__init__(self, parent, id=id, label=texte)
        self.parent = parent
        self.texte = texte
        self.role = role if role in BUTTON_ROLES else "default"
        self._teamworks_text_style = "label"
        self.Bind(wx.EVT_TOGGLEBUTTON, self._OnToggleContract)
        self.MAJ()

    def _OnToggleContract(self, event):
        self.AppliquerTheme()
        self.Refresh(False)
        event.Skip()

    def MAJ(self):
        self.AppliquerTheme()
        try:
            if hasattr(self, "InvalidateBestSize"):
                self.InvalidateBestSize()
            self.Refresh(False)
        except Exception:
            pass

    def RafraichirVisuel(self):
        self.MAJ()

    def AppliquerTheme(self):
        _appliquer_contrat_bouton(
            self,
            texte=self.texte,
            role=self.role,
            icon_only=False,
        )
        if self.GetValue():
            self.SetBackgroundColour(UTILS_Interface.GetToken("primary_container"))
            self.SetForegroundColour(UTILS_Interface.GetToken("on_primary_container"))
        else:
            self.SetBackgroundColour(UTILS_Interface.GetToken("surface_container_low"))
            self.SetForegroundColour(UTILS_Interface.GetToken(_token_texte_bouton(self.role)))

    def SetValue(self, value):
        wx.ToggleButton.SetValue(self, bool(value))
        self.AppliquerTheme()
        self.Refresh(False)

    def SetTexte(self, texte=""):
        self.texte = texte
        self.SetLabel(texte)
        self.MAJ()

    def SetRole(self, role="default"):
        self.role = role if role in BUTTON_ROLES else "default"
        self.AppliquerTheme()
        self.Refresh(False)
