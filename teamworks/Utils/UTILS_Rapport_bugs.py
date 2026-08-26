#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Teamworks CCNS
# Licence :         GNU GPL
#------------------------------------------------------------------------

import os
import sys
import threading

import wx

from Utils.UTILS_Traduction import _
from Utils import UTILS_Blackbox
from Utils import UTILS_Config
from Utils import UTILS_Crash
from Utils import UTILS_Envoi_rapport_bug
from Utils import UTILS_Fichiers


_VERSION_ACTIVE = ""
_ORIGINAL_WX_EXCEPTION_HANDLER = getattr(wx.App, "OnExceptionInMainLoop", None)
_ORIGINAL_WX_MAINLOOP = getattr(wx.App, "MainLoop", None)
_BLACKBOX_FILTER = None
_BLACKBOX_MAINLOOP_WRAPPED = False


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


def _type_exception_sur(exctype):
    nom = getattr(exctype, "__name__", "Exception")
    if isinstance(nom, str) and nom.replace("_", "").isalnum():
        return nom
    return "Exception"


def Rapporter_exception(exctype, value, tb, version=None, contexte="Exception Python", afficher=True):
    """Enregistre une exception sans sérialiser de valeur métier."""
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

    try:
        print("Exception %s — rapport technique créé" % _type_exception_sur(exctype))
    except Exception:
        pass

    if chemin_rapport:
        try:
            with open(chemin_rapport, "r", encoding="utf-8", errors="replace") as fichier:
                rapport = fichier.read()
        except Exception:
            rapport = "Exception technique : %s" % _type_exception_sur(exctype)
        texte = _(
            u"Rapport enregistré : %s\n\n"
            u"Transmettez de préférence ce fichier .txt pour le débogage.\n\n%s"
        ) % (chemin_rapport, rapport)
    else:
        texte = "Exception technique : %s" % _type_exception_sur(exctype)

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


def _binder_type(nom):
    binder = getattr(wx, nom, None)
    return getattr(binder, "typeId", None)


def _wx_component(objet):
    try:
        cls = objet.__class__
        module = getattr(cls, "__module__", "wx")
        nom = getattr(cls, "__name__", "Window")
        return "wx:%s.%s" % (module, nom)
    except Exception:
        return "wx:unknown"


def _menu_component(event_id):
    """Résout uniquement le code technique du menu, jamais son libellé."""
    try:
        app = wx.GetApp()
        top = app.GetTopWindow() if app is not None else None
        infos = getattr(top, "dictInfosMenu", {}) if top is not None else {}
        for code, info in infos.items():
            if isinstance(info, dict) and info.get("id") == event_id:
                return "menu:%s" % code
    except Exception:
        pass
    return "menu:unknown"


class _BlackboxEventFilter(wx.EventFilter):
    """Observe seulement des catégories d'événements, jamais leur contenu."""

    def __init__(self):
        wx.EventFilter.__init__(self)
        self._types = {}
        for binder_name, action in (
            ("EVT_MENU", "MENU"),
            ("EVT_BUTTON", "BUTTON_CLICK"),
            ("EVT_TOOL", "TOOL_CLICK"),
            ("EVT_LEFT_DCLICK", "DOUBLE_CLICK"),
            ("EVT_LIST_ITEM_ACTIVATED", "LIST_ACTIVATE"),
            ("EVT_TREE_ITEM_ACTIVATED", "TREE_ACTIVATE"),
            ("EVT_TOOLBOOK_PAGE_CHANGED", "PAGE_CHANGED"),
            ("EVT_NOTEBOOK_PAGE_CHANGED", "PAGE_CHANGED"),
            ("EVT_WINDOW_CREATE", "WINDOW_CREATE"),
            ("EVT_WINDOW_DESTROY", "WINDOW_DESTROY"),
            ("EVT_SHOW", "WINDOW_VISIBILITY"),
        ):
            event_type = _binder_type(binder_name)
            if event_type is not None:
                self._types[event_type] = action

    def FilterEvent(self, event):
        continuer = getattr(wx.EventFilter, "Event_Skip", -1)
        try:
            action = self._types.get(event.GetEventType())
            if action is None:
                return continuer

            event_id = event.GetId() if hasattr(event, "GetId") else None
            if action == "MENU":
                UTILS_Blackbox.Tracer("MENU", _menu_component(event_id), code=event_id)
                return continuer

            objet = event.GetEventObject() if hasattr(event, "GetEventObject") else None

            if action in ("WINDOW_CREATE", "WINDOW_DESTROY", "WINDOW_VISIBILITY"):
                if objet is None or not isinstance(objet, wx.TopLevelWindow):
                    return continuer
                if action == "WINDOW_VISIBILITY":
                    try:
                        action = "WINDOW_SHOW" if event.IsShown() else "WINDOW_HIDE"
                    except Exception:
                        action = "WINDOW_VISIBILITY"

            component = _wx_component(objet) if objet is not None else "wx:unknown"
            UTILS_Blackbox.Tracer(action, component, code=event_id)
        except Exception:
            # La boîte noire ne doit jamais perturber le traitement d'un événement.
            pass
        return continuer


def Activer_boite_noire_wx(app=None):
    """Active les breadcrumbs wx et le watchdog une fois OnInit terminé."""
    global _BLACKBOX_FILTER
    if _BLACKBOX_FILTER is not None:
        return

    try:
        filtre = _BlackboxEventFilter()
        wx.EvtHandler.AddFilter(filtre)
        _BLACKBOX_FILTER = filtre
    except Exception:
        _BLACKBOX_FILTER = None

    UTILS_Blackbox.Tracer("BLACKBOX_START", "app:wx_main_loop")

    def poster_heartbeat():
        wx.CallAfter(UTILS_Blackbox.MarquerHeartbeat)

    try:
        seuil = float(os.environ.get("TEAMWORKS_FREEZE_THRESHOLD_SECONDS", "8"))
    except Exception:
        seuil = 8.0

    try:
        UTILS_Blackbox.DemarrerWatchdog(
            poster_heartbeat,
            version=_VERSION_ACTIVE,
            seuil_secondes=seuil,
            intervalle_secondes=min(1.0, max(0.05, seuil / 4.0)),
        )
    except Exception:
        pass


def Activer_rapport_erreurs(version=""):
    """Active crash reports, boîte noire technique, wx, threads et faulthandler."""
    global _VERSION_ACTIVE, _BLACKBOX_MAINLOOP_WRAPPED
    _VERSION_ACTIVE = UTILS_Crash.GetVersionApplication(version)

    # Si Chemins.py ne l'a pas déjà fait, active aussi la capture des erreurs
    # fatales C/Python (segfault, abort, etc.).
    UTILS_Crash.ActiverFaulthandler(version=_VERSION_ACTIVE)

    def my_excepthook(exctype, value, tb):
        Rapporter_exception(exctype, value, tb, contexte="Exception Python")

    sys.excepthook = my_excepthook

    if hasattr(threading, "excepthook"):
        def thread_excepthook(args):
            Rapporter_exception(
                args.exc_type,
                args.exc_value,
                args.exc_traceback,
                contexte="Thread Python",
                afficher=True,
            )
        threading.excepthook = thread_excepthook

    if hasattr(sys, "unraisablehook"):
        def unraisable_hook(args):
            exc_type = type(args.exc_value) if args.exc_value is not None else RuntimeError
            exc_value = args.exc_value or RuntimeError("Exception non remontable")
            Rapporter_exception(
                exc_type,
                exc_value,
                args.exc_traceback,
                contexte="Exception non remontable",
                afficher=False,
            )
        sys.unraisablehook = unraisable_hook

    # wxPython intercepte certaines exceptions d'événements à l'intérieur de sa
    # boucle principale sans nécessairement passer par sys.excepthook.
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
        pass

    # Le watchdog doit commencer après MyApp.OnInit. En enveloppant MainLoop,
    # l'initialisation (assistant, splash, ouverture initiale) ne peut pas être
    # prise à tort pour un freeze de l'interface.
    if not _BLACKBOX_MAINLOOP_WRAPPED and _ORIGINAL_WX_MAINLOOP is not None:
        def mainloop_with_blackbox(app_self, *args, **kwargs):
            try:
                Activer_boite_noire_wx(app_self)
            except Exception:
                pass
            return _ORIGINAL_WX_MAINLOOP(app_self, *args, **kwargs)

        try:
            wx.App.MainLoop = mainloop_with_blackbox
            _BLACKBOX_MAINLOOP_WRAPPED = True
        except Exception:
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
                u"Un rapport technique sans données utilisateur a été enregistré automatiquement. "
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
        self.bouton_envoyer = wx.Button(self, wx.ID_ANY, _(u"Envoyer le rapport"))
        self.bouton_fermer = wx.Button(self, wx.ID_CANCEL, _(u"Fermer"))

        self.label_titre.SetFont(self.label_titre.GetFont().Bold())
        self.SetMinSize((760, 500))

        self.Bind(wx.EVT_BUTTON, self.OnBoutonDossier, self.bouton_dossier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonCopier, self.bouton_copier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEnvoyer, self.bouton_envoyer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFermer, self.bouton_fermer)

        self.bouton_envoyer.Enable(bool(chemin_rapport and os.path.isfile(chemin_rapport)))

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
        boutons.Add(self.bouton_envoyer, 0, wx.RIGHT, 8)
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

    def OnBoutonEnvoyer(self, event):
        destinataire = UTILS_Envoi_rapport_bug.DESTINATAIRE_RAPPORTS_BUGS
        confirmation = wx.MessageDialog(
            self,
            _(
                u"Envoyer le rapport technique à %s ?\n\n"
                u"Seul le fichier .txt affiché sera joint. Il ne contient ni donnée "
                u"métier ni contenu de la base. L'adresse expéditeur par défaut de "
                u"Teamworks sera utilisée."
            ) % destinataire,
            _(u"Envoi du rapport de crash"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        reponse = confirmation.ShowModal()
        confirmation.Destroy()
        if reponse != wx.ID_YES:
            return

        self.bouton_envoyer.Enable(False)
        try:
            wx.BeginBusyCursor()
            UTILS_Envoi_rapport_bug.EnvoyerRapport(
                self.chemin_rapport,
                version=_VERSION_ACTIVE,
            )
        except UTILS_Envoi_rapport_bug.ErreurEnvoiRapport as err:
            wx.MessageBox(
                _(u"Le rapport n'a pas été envoyé.\n\n%s\n\nLe fichier reste disponible dans Logs.") % err,
                _(u"Envoi impossible"),
                wx.OK | wx.ICON_ERROR,
                parent=self,
            )
        else:
            wx.MessageBox(
                _(u"Le rapport a bien été envoyé à %s.") % destinataire,
                _(u"Rapport envoyé"),
                wx.OK | wx.ICON_INFORMATION,
                parent=self,
            )
        finally:
            if wx.IsBusy():
                wx.EndBusyCursor()
            self.bouton_envoyer.Enable(True)

    def OnBoutonFermer(self, event):
        self.EndModal(wx.ID_CANCEL)


if __name__ == u"__main__":
    app = wx.App(0)
    dialog = DLG_Rapport(None, texte="Exemple de rapport")
    app.SetTopWindow(dialog)
    dialog.ShowModal()
