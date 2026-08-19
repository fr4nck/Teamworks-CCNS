#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-17 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import datetime
import sys
from importlib import import_module

import wx


def _install_native_checklist_bridge():
    """Neutralise les anciennes cases du CheckListCtrlMixin sous Phoenix.

    Plusieurs écrans historiques héritent encore de ``CheckListCtrlMixin`` tout
    en activant les cases natives de ``wx.ListCtrl``. Sous Phoenix cela affiche
    deux colonnes de cases à cocher. Le pont conserve temporairement l'API du
    mixin utilisée par ces écrans (``ToggleItem`` et ``IsChecked``), mais laisse
    exclusivement wxPython gérer l'affichage et l'état des cases.
    """
    try:
        from wx.lib.mixins import listctrl as listmix
    except ImportError:
        return

    mixin = listmix.CheckListCtrlMixin
    if getattr(mixin, "_teamworks_native_checkbox_bridge", False):
        return

    def native_init(self):
        # Ne crée aucune ImageList de checkbox : wx.ListCtrl affiche ses cases
        # natives via EnableCheckBoxes(True), déjà appelé par les écrans.
        def on_checked(event):
            callback = getattr(self, "OnCheckItem", None)
            if callable(callback):
                callback(event.GetIndex(), True)
            event.Skip()

        def on_unchecked(event):
            callback = getattr(self, "OnCheckItem", None)
            if callable(callback):
                callback(event.GetIndex(), False)
            event.Skip()

        self.Bind(wx.EVT_LIST_ITEM_CHECKED, on_checked)
        self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, on_unchecked)

    def native_toggle_item(self, index):
        self.CheckItem(index, not self.IsItemChecked(index))

    def native_is_checked(self, index):
        return self.IsItemChecked(index)

    mixin.__init__ = native_init
    mixin.ToggleItem = native_toggle_item
    mixin.IsChecked = native_is_checked
    mixin._teamworks_native_checkbox_bridge = True


_install_native_checklist_bridge()


def _safe_person_age(self, date_value):
    """Retourne un âge lisible sans bloquer sur une date historique invalide."""
    if not date_value:
        return ""

    if isinstance(date_value, datetime.datetime):
        birth_date = date_value.date()
    elif isinstance(date_value, datetime.date):
        birth_date = date_value
    else:
        try:
            birth_date = datetime.date.fromisoformat(str(date_value).strip()[:10])
        except (TypeError, ValueError, OverflowError):
            return ""

    today = datetime.date.today()
    if birth_date > today:
        return ""
    age = today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )
    return "%d ans" % age


def _apply_runtime_guards(module, nom_module):
    """Applique les protections ciblées aux modules historiques importés."""
    if nom_module.endswith("OL_personnes") and hasattr(module, "Track"):
        module.Track.RetourneAge = _safe_person_age
    return module


def Import(nom_module=""):
    # Essaye d'importer
    try:
        module = import_module(nom_module)
        return _apply_runtime_guards(module, nom_module)
    except ImportError:
        pass

    # Recherche si le module est déjà chargé
    if nom_module in sys.modules:
        return _apply_runtime_guards(sys.modules[nom_module], nom_module)

    # Essaye d'importer sans le module_path
    _, class_name = nom_module.rsplit('.', 1)
    try:
        module = import_module(class_name)
        return _apply_runtime_guards(module, nom_module)
    except ImportError:
        return None


class Menu(wx.Menu):
    def __init__(self, *args, **kwds):
        wx.Menu.__init__(self, *args, **kwds)

    def AppendItem(self, item):
        super(Menu, self).Append(item)

    def AppendMenu(self, *args, **kwargs):
        super(Menu, self).Append(*args, **kwargs)


class ToolBar(wx.ToolBar):
    def __init__(self, *args, **kwds):
        wx.ToolBar.__init__(self, *args, **kwds)

    def AddLabelTool(self, *args, **kw):
        kw.pop("longHelp", None)
        super(ToolBar, self).AddTool(*args, **kw)

    def AddSimpleTool(self, *args, **kw):
        kw.pop("longHelp", None)
        super(ToolBar, self).AddTool(*args, **kw)

    def AddTool(self, *args, **kw):
        shortHelp = kw.pop("shortHelpString", "")
        toolId = args[0]
        bitmap = args[1]
        super(ToolBar, self).AddTool(
            toolId=toolId,
            label="",
            bitmap=bitmap,
            shortHelp=shortHelp,
        )


if __name__ == "__main__":
    pass
