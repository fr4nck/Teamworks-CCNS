#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Teamworks CCNS
# Licence :         GNU GPL
#------------------------------------------------------------------------

import os
import sys
import threading
import traceback

import wx

from Utils.UTILS_Traduction import _
from Utils import UTILS_Config
from Utils import UTILS_Crash
from Utils import UTILS_Fichiers


_VERSION_ACTIVE = ""
_ORIGINAL_WX_EXCEPTION_HANDLER = getattr(wx.App, "OnExceptionInMainLoop", None)


def _copier_texte(texte):
    try:
        if not wx.TheClipboard.Open():
            return False
        try:
            data = wx.TextDataObject()
            data.SetText(texte)
            wx.TheClipboard.SetData(data)
            return True
        finally:
            wx.TheClipboard.Close()
    except Exception:
        return False


def _afficher_dialogue(texte, chemin_rapport):
    try:
        dlg = DLG_Rapport(None, texte=texte, chemin_rapport=chemin_rapport)
        dlg.ShowModal()
        dlg.Destroy()
    except Exception:
        # Le rapport est déjà écrit sur disque : une défaillance du dialogue ne
        # doit jamais masquer l'exception d'origine.
        pass


def Rapporter_exception(exctype, value, tb, version=None, contexte="Exception Python", afficher=True):
    """Enregistre une exception et, si possible, affiche le rapport à l'utilisateur."""
    version = _VERSION_ACTIVE if version is None else version
    try:
        version_wx = wx.version()
    except Exception:
        version_wx = ""

    try:
        chemin_rapport = UTILS_Crash.EcrireRapportException(
            exctype,
            value,
            tb,
            version=version or "",
            contexte=contexte,
            version_wx=version_wx,
        )
    except Exception:
        chemin_rapport = ""

    bug = "".join(traceback.format_exception(exctype, value, tb))
    try:
        print(bug)
    except Exception:
        pass

    if chemin_rapport:
        try:
            with open(chemin_rapport, "r", encoding="utf-8", errors="replace") as fichier:
                rapport = fichier.read()
        except Exception:
            rapport = bug
        texte = _(
            u"Rapport enregistré : %s\n\n"
            u"Transmettez de préférence ce fichier .txt pour le débogage.\n\n%s"
        ) % (chemin_rapport, rapport)
    else:
        texte = bug

    if not afficher:
        return chemin_rapport

    try:
        if UTILS_Config.GetParametre("rapports_bugs", True) is False:
            return chemin_rapport
    except Exception:
        pass

    try:
        app = wx.GetApp()
        if app is None:
            return chemin_rapport
        if threading.current_thread() is threading.main_thread():
            _afficher_dialogue(texte, chemin_rapport)
        else:
            wx.CallAfter(_afficher_dialogue, texte, chemin_rapport)
    except Exception:
        pass

    return chemin_rapport


def Activer_rapport_erreurs(version=""):
    """Active les diagnostics Python, wx, threads et erreurs fatales."""
    global _VERSION_ACTIVE
    _VERSION_ACTIVE = version or ""

    # Si Chemins.py ne l'a pas déjà fait, active aussi la capture des erreurs
    # fatales C/Python (segfault, abort, etc.).
    UTILS_Crash.ActiverFaulthandler(version=_VERSION_ACTIVE)

    def my_excepthook(exctype, value, tb):
        Rapporter_exception(exctype, value, tb, contexte="Exception Python")

    sys.excepthook = my_excepthook

    if hasattr(threading, "excepthook"):
        def thread_excepthook(args):
            nom_thread = getattr(args.thread, "name", "thread") if args.thread is not None else "thread"
            Rapporter_exception(
                args.exc_type,
                args.exc_value,
                args.exc_traceback,
                contexte="Thread : %s" % nom_thread,
                afficher=True,
            )
        threading.excepthook = thread_excepthook

    if hasattr(sys, "unraisablehook"):
        def unraisable_hook(args):
            exc_type = type(args.exc_value) if args.exc_value is not None else RuntimeError
            exc_value = args.exc_value or RuntimeError(str(args.err_msg or "Exception non remontable"))
            Rapporter_exception(
                exc_type,
                exc_value,
                args.exc_traceback,
                contexte="Exception non remontable",
                afficher=False,
            )
        sys.unraisablehook = unraisable_hook

    # wxPython intercepte certaines exceptions d'événements à l'intérieur de sa
    # boucle principale sans nécessairement passer par sys.excepthook. On pose
    # donc le même rapporteur au niveau de wx.App avant l'instanciation de MyApp.
    def wx_exception_handler(app_self):
        exctype, value, tb = sys.exc_info()
        if exctype is not None:
            Rapporter_exception(
                exctype,
                value,
                tb,
                contexte="Boucle wxPython",
                afficher=True,
            )
            return True
        if _ORIGINAL_WX_EXCEPTION_HANDLER is not None:
            try:
                return _ORIGINAL_WX_EXCEPTION_HANDLER(app_self)
            except Exception:
                pass
        return False

    try:
        wx.App.OnExceptionInMainLoop = wx_exception_handler
    except Exception:
        # Le hook sys + le rapport natif restent actifs même si une version de
        # wxPython refuse le remplacement de cette méthode.
        pass


# ------------------------------------------- BOITE DE DIALOGUE ----------------------------------------------------------------------------------------

class DLG_Rapport(wx.Dialog):
    def __init__(self, parent, texte="", chemin_rapport=""):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            title=_(u"Rapport de crash Teamworks CCNS"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )
        self.chemin_rapport = chemin_rapport

        self.label_titre = wx.StaticText(self, wx.ID_ANY, _(u"Teamworks CCNS a rencontré un problème."))
        self.label_info = wx.StaticText(
            self,
            wx.ID_ANY,
            _(
                u"Un rapport a été enregistré automatiquement. "
                u"Pour faciliter le débogage, transmettez le fichier .txt du dossier Logs."
            ),
        )
        self.ctrl_rapport = wx.TextCtrl(
            self,
            wx.ID_ANY,
            texte,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL,
        )

        self.bouton_dossier = wx.Button(self, wx.ID_ANY, _(u"Ouvrir le dossier Logs"))
        self.bouton_copier = wx.Button(self, wx.ID_ANY, _(u"Copier le rapport"))
        self.bouton_fermer = wx.Button(self, wx.ID_CANCEL, _(u"Fermer"))

        self.label_titre.SetFont(self.label_titre.GetFont().Bold())
        self.SetMinSize((760, 500))

        self.Bind(wx.EVT_BUTTON, self.OnBoutonDossier, self.bouton_dossier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonCopier, self.bouton_copier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFermer, self.bouton_fermer)

        self.__do_layout()
        _copier_texte(texte)
        self.bouton_fermer.SetFocus()

    def __do_layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label_titre, 0, wx.LEFT | wx.RIGHT | wx.TOP, 12)
        sizer.Add(self.label_info, 0, wx.LEFT | wx.RIGHT | wx.TOP, 12)
        sizer.Add(self.ctrl_rapport, 1, wx.ALL | wx.EXPAND, 12)

        boutons = wx.BoxSizer(wx.HORIZONTAL)
        boutons.Add(self.bouton_dossier, 0, wx.RIGHT, 8)
        boutons.Add(self.bouton_copier, 0, wx.RIGHT, 8)
        boutons.AddStretchSpacer(1)
        boutons.Add(self.bouton_fermer, 0)
        sizer.Add(boutons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)

        self.SetSizer(sizer)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonDossier(self, event):
        try:
            if self.chemin_rapport:
                repertoire = os.path.dirname(self.chemin_rapport)
            else:
                repertoire = UTILS_Crash.GetRepertoireLogs()
            UTILS_Fichiers.OuvrirRepertoire(repertoire)
        except Exception as err:
            wx.MessageBox(
                _(u"Impossible d'ouvrir le dossier des diagnostics : %s") % err,
                _(u"Diagnostics"),
                wx.OK | wx.ICON_ERROR,
                parent=self,
            )

    def OnBoutonCopier(self, event):
        _copier_texte(self.ctrl_rapport.GetValue())

    def OnBoutonFermer(self, event):
        self.EndModal(wx.ID_CANCEL)


if __name__ == u"__main__":
    app = wx.App(0)
    dialog = DLG_Rapport(None, texte="Exemple de rapport")
    app.SetTopWindow(dialog)
    dialog.ShowModal()
