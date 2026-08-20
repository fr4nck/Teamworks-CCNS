#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adaptations géométriques progressives de l'interface historique.

Cette couche ne remplace pas les écrans wx existants : elle corrige leurs
contraintes figées au moment où ils deviennent visibles. Les règles restent
volontairement défensives et ciblent les familles de contrôles historiques
connues de Teamworks.
"""

from __future__ import annotations

import wx


_PATCHED = False


def _font_scale():
    try:
        from Utils import UTILS_Theme
        return max(80, min(200, int(UTILS_Theme.font_scale_percent())))
    except Exception:
        return 100


def _bind_size_once(window, callback, marker):
    if getattr(window, marker, False):
        return
    setattr(window, marker, True)

    def _on_size(event):
        try:
            wx.CallAfter(callback, window)
        except Exception:
            pass
        event.Skip()

    try:
        window.Bind(wx.EVT_SIZE, _on_size)
    except Exception:
        pass


def _bitmap_button_bitmap(button):
    for getter_name in ("GetBitmap", "GetBitmapLabel"):
        getter = getattr(button, getter_name, None)
        if getter is None:
            continue
        try:
            bitmap = getter()
            if bitmap and bitmap.IsOk():
                return bitmap
        except Exception:
            pass
    return None


def _set_bitmap_button_bitmap(button, bitmap):
    for setter_name in ("SetBitmap", "SetBitmapLabel"):
        setter = getattr(button, setter_name, None)
        if setter is None:
            continue
        try:
            setter(bitmap)
            return True
        except Exception:
            pass
    return False


def _adapt_bitmap_button(button):
    """Rend les anciennes actions 16x16 réellement manipulables."""
    scale = _font_scale() / 100.0
    icon_size = max(24, min(32, int(round(24 * scale))))
    side = max(36, icon_size + 12)

    if not getattr(button, "_teamworks_bitmap_scaled", False):
        bitmap = _bitmap_button_bitmap(button)
        if bitmap is not None:
            try:
                if bitmap.GetWidth() < icon_size or bitmap.GetHeight() < icon_size:
                    image = bitmap.ConvertToImage()
                    image = image.Scale(icon_size, icon_size, wx.IMAGE_QUALITY_HIGH)
                    _set_bitmap_button_bitmap(button, wx.Bitmap(image))
            except Exception:
                pass
        button._teamworks_bitmap_scaled = True

    try:
        button.SetMinSize((side, side))
    except Exception:
        pass


def _column_headers(listctrl):
    headers = []
    try:
        count = listctrl.GetColumnCount()
    except Exception:
        return headers
    for index in range(count):
        try:
            headers.append(listctrl.GetColumn(index).GetText())
        except Exception:
            headers.append("")
    return headers


def _fit_list_columns(listctrl):
    """Utilise l'espace libre sans compresser les colonnes en cas de manque.

    Les largeurs historiques servent de minimum logique. Le facteur de police
    augmente ce minimum ; si la fenêtre offre davantage d'espace, le surplus
    est distribué aux colonnes de contenu plutôt que laissé en zone blanche.
    """
    if getattr(listctrl, "_teamworks_fitting_columns", False):
        return
    try:
        count = listctrl.GetColumnCount()
        if count <= 0:
            return
        width = listctrl.GetClientSize().GetWidth()
        if width <= 80:
            return
    except Exception:
        return

    headers = _column_headers(listctrl)
    signature = tuple(headers)
    baseline = getattr(listctrl, "_teamworks_column_baseline", None)
    if not baseline or baseline[0] != signature:
        widths = []
        for index in range(count):
            try:
                widths.append(max(22, int(listctrl.GetColumnWidth(index))))
            except Exception:
                widths.append(80)
        baseline = (signature, widths)
        listctrl._teamworks_column_baseline = baseline

    base_widths = baseline[1]
    scale = _font_scale() / 100.0
    desired = [max(22, int(round(value * scale))) for value in base_widths]

    try:
        scrollbar = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
        if scrollbar <= 0:
            scrollbar = 18
    except Exception:
        scrollbar = 18
    available = max(60, width - scrollbar - 6)
    total = sum(desired)

    # Ne jamais écraser les données pour forcer un tableau dans une fenêtre trop
    # étroite : le scroll horizontal est préférable à des colonnes illisibles.
    target = list(desired)
    if available > total:
        flexible = [
            index
            for index, value in enumerate(desired)
            if value >= 80 and headers[index].strip().lower() not in {
                "âge", "cp", "civilité", "due", "signé", "signature"
            }
        ]
        if not flexible:
            flexible = [count - 1]
        extra = available - total
        weight = sum(max(1, desired[index]) for index in flexible)
        assigned = 0
        for position, index in enumerate(flexible):
            if position == len(flexible) - 1:
                addition = extra - assigned
            else:
                addition = int(extra * desired[index] / weight)
                assigned += addition
            target[index] += max(0, addition)

    listctrl._teamworks_fitting_columns = True
    try:
        for index, column_width in enumerate(target):
            try:
                if listctrl.GetColumnWidth(index) != column_width:
                    listctrl.SetColumnWidth(index, column_width)
            except Exception:
                pass
    finally:
        listctrl._teamworks_fitting_columns = False


def _adapt_listctrl(listctrl):
    _bind_size_once(listctrl, _fit_list_columns, "_teamworks_list_size_bound")
    try:
        wx.CallAfter(_fit_list_columns, listctrl)
    except Exception:
        pass


def _detach_useless_persons_filler(panel):
    filler = getattr(panel, "panel_vide", None)
    multisplitter = getattr(panel, "window_G", None)
    if filler is None or multisplitter is None:
        return
    if getattr(panel, "_teamworks_filler_detached", False):
        return

    try:
        detach = getattr(multisplitter, "DetachWindow", None)
        if detach is not None:
            detach(filler)
        filler.Hide()
        panel._teamworks_filler_detached = True
    except Exception:
        # Le simple masquage améliore déjà le cas des ports wx qui n'exposent
        # pas DetachWindow sur MultiSplitterWindow.
        try:
            filler.Hide()
            panel._teamworks_filler_detached = True
        except Exception:
            pass


def _adapt_persons_sidebar(panel):
    """Réduit le remplissage historique et rend le splitter utile."""
    _detach_useless_persons_filler(panel)

    splitter = getattr(panel, "splitter", None)
    if splitter is not None:
        try:
            splitter.SetMinimumPaneSize(180)
            splitter.SetSashGravity(0.0)
            width = panel.GetClientSize().GetWidth()
            current = splitter.GetSashPosition()
            minimum = 190
            maximum = min(360, max(240, int(width * 0.28)))
            if not getattr(panel, "_teamworks_sash_initialized", False):
                target = min(maximum, max(230, int(width * 0.18)))
                splitter.SetSashPosition(target, True)
                panel._teamworks_sash_initialized = True
            elif current < minimum:
                splitter.SetSashPosition(minimum, True)
            elif current > maximum:
                splitter.SetSashPosition(maximum, True)
        except Exception:
            pass

    # Le bleu plein historique transforme quelques lignes d'information en un
    # grand pavé visuel. Une surface neutre garde l'information sans le remplissage.
    dossiers = getattr(panel, "panel_dossiers", None)
    if dossiers is not None:
        try:
            from Utils import UTILS_Interface
            surface = UTILS_Interface.GetToken("surface")
            control = UTILS_Interface.GetToken("surface_container_lowest")
            dossiers.SetBackgroundColour(surface)
            tree = getattr(dossiers, "tree_ctrl_problemes", None)
            if tree is not None:
                tree.couleurFond = (control.Red(), control.Green(), control.Blue())
                tree.SetBackgroundColour(control)
                tree.Refresh()
        except Exception:
            pass

    try:
        panel.Layout()
    except Exception:
        pass


def _adapt_persons_panel(panel):
    _adapt_persons_sidebar(panel)
    _bind_size_once(panel, _adapt_persons_sidebar, "_teamworks_persons_size_bound")

    for name in (
        "bouton_ajouter", "bouton_modifier", "bouton_supprimer",
        "bouton_rechercher", "bouton_affichertout", "bouton_options",
        "bouton_courrier", "bouton_imprimer", "bouton_export_texte",
        "bouton_export_excel", "bouton_aide",
    ):
        button = getattr(panel, name, None)
        if isinstance(button, wx.BitmapButton):
            _adapt_bitmap_button(button)

    # L'ancien FlexGridSizer rendait la ligne du bouton supprimer extensible,
    # ce qui créait un espace arbitraire dans la barre d'actions.
    button = getattr(panel, "bouton_supprimer", None)
    if button is not None:
        try:
            sizer = button.GetContainingSizer()
            remove = getattr(sizer, "RemoveGrowableRow", None)
            if remove is not None:
                remove(2)
        except Exception:
            pass


def _adapt_contract_page(panel):
    for name in (
        "bouton_contrats_ajouter", "bouton_contrats_modifier",
        "bouton_contrats_supprimer", "bouton_signature",
        "bouton_due", "bouton_imprimer",
    ):
        button = getattr(panel, name, None)
        if isinstance(button, wx.BitmapButton):
            _adapt_bitmap_button(button)

    listctrl = getattr(panel, "list_ctrl_contrats", None)
    if isinstance(listctrl, wx.ListCtrl):
        _adapt_listctrl(listctrl)


def _adapt_person_dialog(dialog):
    """Donne à la fiche individuelle une taille initiale utile et fluide."""
    if getattr(dialog, "_teamworks_initial_dialog_size", False):
        return
    dialog._teamworks_initial_dialog_size = True
    try:
        display_index = wx.Display.GetFromWindow(dialog)
        if display_index == wx.NOT_FOUND:
            display_index = 0
        area = wx.Display(display_index).GetClientArea()
        width = min(1280, max(900, int(area.GetWidth() * 0.72)))
        height = min(900, max(680, int(area.GetHeight() * 0.78)))
        current = dialog.GetSize()
        if current.GetWidth() < width or current.GetHeight() < height:
            dialog.SetSize((max(current.GetWidth(), width), max(current.GetHeight(), height)))
            dialog.CentreOnParent()
    except Exception:
        pass


def _adapt_one(window):
    try:
        name = window.GetName()
    except Exception:
        name = ""

    if isinstance(window, wx.BitmapButton):
        _adapt_bitmap_button(window)
    if isinstance(window, wx.ListCtrl):
        _adapt_listctrl(window)

    if name == "Personnes" or (
        hasattr(window, "listCtrl_personnes") and hasattr(window, "panel_dossiers")
    ):
        _adapt_persons_panel(window)
    elif name == "page_contrats":
        _adapt_contract_page(window)
    elif name == "FicheIndividuelle":
        _adapt_person_dialog(window)


def apply_to_window_tree(window):
    if window is None:
        return
    _adapt_one(window)
    try:
        children = window.GetChildren()
    except Exception:
        children = []
    for child in children:
        apply_to_window_tree(child)
    try:
        window.Layout()
    except Exception:
        pass


def install_auto_layout():
    """Installe le reflow après le hook de thème existant."""
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    original_show = wx.Window.Show

    def responsive_show(window, *args, **kwargs):
        result = original_show(window, *args, **kwargs)
        try:
            wx.CallAfter(apply_to_window_tree, window)
        except Exception:
            pass
        return result

    wx.Window.Show = responsive_show

    original_show_modal = wx.Dialog.ShowModal

    def responsive_show_modal(dialog, *args, **kwargs):
        try:
            apply_to_window_tree(dialog)
        except Exception:
            pass
        return original_show_modal(dialog, *args, **kwargs)

    wx.Dialog.ShowModal = responsive_show_modal
