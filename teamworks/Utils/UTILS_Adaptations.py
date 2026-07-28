#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-17 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import sys
from importlib import import_module

import wx


def Import(nom_module=""):
    # Essaye d'importer
    try:
        return import_module(nom_module)
    except ImportError:
        pass

    # Recherche si le module est déjà chargé
    if nom_module in sys.modules:
        return sys.modules[nom_module]

    # Essaye d'importer sans le module_path
    _, class_name = nom_module.rsplit('.', 1)
    try:
        return import_module(class_name)
    except ImportError:
        return None


class Menu(wx.Menu):
    def __init__(self, *args, **kwds):
        wx.Menu.__init__(self, *args, **kwds)

    def AppendItem(self, item):
        super(Menu, self).Append(item)

    def AppendMenu(self, *args, **kwds):
        super(Menu, self).Append(*args, **kwds)


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
