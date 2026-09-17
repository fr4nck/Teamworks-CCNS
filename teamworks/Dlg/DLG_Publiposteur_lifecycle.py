# -*- coding: utf-8 -*-
"""Correctifs RC2 de cycle de vie pour le publipostage Word/Writer.

Le module historique garde son API. Ce patch isole l'automatisation externe dans
un unique worker propriétaire de ses objets COM, et ne laisse jamais ce worker
manipuler directement des contrôles wx.
"""

from __future__ import annotations

import copy
import gc
import os
import threading


class _PublipostageFailure(RuntimeError):
    def __init__(self, message, document_id=None):
        super(_PublipostageFailure, self).__init__(message)
        self.document_id = document_id


def _as_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def normalize_merge_documents(dict_donnees):
    """Retourne un snapshot sans ``None`` utilisable par Word/UNO.

    Les objets wx et la base ne doivent jamais être relus depuis le worker. Le
    snapshot contient donc uniquement des primitives et une copie des valeurs
    de fusion au moment où l'utilisateur lance le traitement.
    """
    if not isinstance(dict_donnees, dict):
        return {}
    result = copy.deepcopy(dict_donnees)
    count = int(result.get("NBREDOCUMENTS", 0) or 0)
    advertised = [
        item[0]
        for item in result.get("MOTSCLES", ())
        if isinstance(item, (tuple, list)) and item
    ]
    for document_id in range(1, count + 1):
        document = result.get(document_id)
        if not isinstance(document, dict):
            document = {}
            result[document_id] = document
        for keyword in advertised:
            document.setdefault(keyword, "")
        for keyword, value in list(document.items()):
            if isinstance(keyword, str) and not keyword.startswith("_"):
                document[keyword] = _as_text(value)
    return result


def _thread_is_alive(thread):
    return bool(thread is not None and thread.is_alive())


def _snapshot_job(module, page):
    wizard = page.GetGrandParent()
    page4 = wizard.page4
    page5 = wizard.page5
    data = normalize_merge_documents(module.DICT_DONNEES)
    count = int(data.get("NBREDOCUMENTS", 0) or 0)
    documents = {}
    for document_id in range(1, count + 1):
        documents[document_id] = [
            (keyword, value)
            for keyword, value in data.get(document_id, {}).items()
            if isinstance(keyword, str) and not keyword.startswith("_")
        ]

    save_enabled = bool(page5.checkbox_save.GetValue())
    names = {}
    if save_enabled:
        names = copy.deepcopy(page5.ctrl_nom_fichiers.GetDictNomsFichiers())

    return {
        "software": int(page.choixLogiciel),
        "count": count,
        "documents": documents,
        "model_path": os.path.join(page4.cheminDest, page4.nomFichier),
        "save": save_enabled,
        "save_names": names,
        "directory": _as_text(page5.text_repertoire.GetValue()),
        "extension": _as_text(page5.extension),
        "print": bool(page5.checkbox_impression.GetValue()),
        "copies": int(page5.combo_box_exemplaires.GetStringSelection() or 1),
        "printer": _as_text(page5.combo_box_imprimante.GetStringSelection()),
        "preview": bool(page5.checkbox_apercu.GetValue()),
    }


def _post(module, callback, *args):
    try:
        module.wx.CallAfter(callback, *args)
    except Exception:
        # Le processus peut être en train de se fermer. Aucun appel wx direct
        # depuis le worker n'est utilisé comme repli.
        pass


def _publisher_error(publisher, document_id=None):
    message = getattr(publisher, "erreur", None)
    if message:
        raise _PublipostageFailure(_as_text(message), document_id=document_id)


def _finalize_word(module, publisher, keep_open=False):
    if getattr(publisher, "_rc2_finalized", False):
        return
    publisher._rc2_finalized = True
    try:
        document = getattr(publisher, "doc", None)
        if document is not None and not keep_open:
            try:
                document.Close(SaveChanges=0)
            except Exception:
                pass
        word = getattr(publisher, "Word", None)
        if word is not None:
            if keep_open:
                try:
                    word.Visible = True
                except Exception:
                    pass
            else:
                try:
                    word.Quit()
                except Exception:
                    pass
    finally:
        publisher.doc = None
        publisher.Word = None
        gc.collect()
        if getattr(publisher, "_rc2_com_initialized", False):
            publisher._rc2_com_initialized = False
            try:
                module.CoUninitialize()
            except Exception:
                pass


def _finalize_writer(module, publisher, keep_open=False):
    if getattr(publisher, "_rc2_finalized", False):
        return
    publisher._rc2_finalized = True
    try:
        document = getattr(publisher, "objDocument", None)
        if document is not None and not keep_open:
            try:
                document.Close(False)
            except Exception:
                pass
        desktop = getattr(publisher, "objDesktop", None)
        if desktop is not None and not keep_open:
            try:
                desktop.Terminate()
            except Exception:
                pass
    finally:
        publisher.objDocument = None
        publisher.objDesktop = None
        gc.collect()
        if getattr(publisher, "_rc2_com_initialized", False):
            publisher._rc2_com_initialized = False
            try:
                module.CoUninitialize()
            except Exception:
                pass


def _finalize_publisher(module, publisher, software, keep_open=False):
    if publisher is None:
        return
    if software == 1:
        _finalize_word(module, publisher, keep_open=keep_open)
    elif software == 2:
        _finalize_writer(module, publisher, keep_open=keep_open)


class _PublipostageWorker(threading.Thread):
    def __init__(self, module, page, job, cancel_event, continue_event):
        super(_PublipostageWorker, self).__init__(name="TeamworksPublipostage")
        self._module = module
        self._page = page
        self._job = job
        self._cancel_event = cancel_event
        self._continue_event = continue_event
        self.stop = False

    def abort(self):
        """Compatibilité avec l'ancienne API : demande d'arrêt, sans toucher wx."""
        self.stop = True
        self._cancel_event.set()
        self._continue_event.set()

    def _check_cancelled(self):
        if self.stop or self._cancel_event.is_set():
            raise _PublipostageFailure("Publipostage interrompu par l'utilisateur.")

    def _progress(self, document_id, state, info, intro=None):
        _post(self._module, self._page._rc2_progress, document_id, state, info, intro)

    def _advance(self):
        _post(self._module, self._page._rc2_advance)

    def run(self):
        module = self._module
        page = self._page
        job = self._job
        publisher = None
        current_document = None
        success = False
        interrupted = False
        error_message = ""
        try:
            self._check_cancelled()
            if job["software"] == 1:
                publisher = module.Publipostage_Word(page)
            else:
                publisher = module.Publipostage_Writer_Windows(page)
            publisher._rc2_worker_managed = True
            publisher.OuvertureLogiciel()
            _publisher_error(publisher)

            for document_id in range(1, job["count"] + 1):
                current_document = document_id
                self._check_cancelled()

                self._progress(
                    document_id,
                    "actuel",
                    module._(u"Création du document"),
                    module._(u"Opération en cours : Création du document n°%d") % document_id,
                )
                publisher.CreationDocument(cheminModele=job["model_path"])
                _publisher_error(publisher, document_id)
                self._check_cancelled()

                self._progress(
                    document_id,
                    "actuel",
                    module._(u"Remplacement des valeurs"),
                    module._(u"Opération en cours : Remplacement des valeurs du document n°%d") % document_id,
                )
                publisher.RemplacementValeurs(listeValeurs=job["documents"].get(document_id, ()))
                _publisher_error(publisher, document_id)
                self._check_cancelled()

                save_info = job["save_names"].get(document_id, {}) if job["save"] else {}
                if job["save"] and save_info.get("SELECTION") == 1:
                    self._progress(
                        document_id,
                        "actuel",
                        module._(u"Sauvegarde du document"),
                        module._(u"Opération en cours : Sauvegarde du document n°%d") % document_id,
                    )
                    filename = _as_text(save_info.get("NOMFICHIER")) + job["extension"]
                    publisher.SauvegardeDocument(os.path.join(job["directory"], filename))
                    _publisher_error(publisher, document_id)
                else:
                    self._advance()
                self._check_cancelled()

                if job["print"]:
                    self._progress(
                        document_id,
                        "actuel",
                        module._(u"Impression du document"),
                        module._(u"Opération en cours : Impression du document n°%d") % document_id,
                    )
                    publisher.ImprimerDocument(job["printer"], job["copies"])
                    _publisher_error(publisher, document_id)
                else:
                    self._advance()
                self._check_cancelled()

                if job["preview"]:
                    self._progress(
                        document_id,
                        "actuel",
                        module._(u"Apercu du document"),
                        module._(u"Opération en cours : Aperçu du document n°%d") % document_id,
                    )
                    publisher.ApercuDocument()
                    _publisher_error(publisher, document_id)
                    if document_id < job["count"]:
                        self._continue_event.clear()
                        _post(module, page._rc2_set_paused, True)
                        while not self._continue_event.wait(0.1):
                            self._check_cancelled()
                        self._check_cancelled()
                        _post(module, page._rc2_set_paused, False)
                        publisher.FermerDocument()
                        _publisher_error(publisher, document_id)
                else:
                    self._progress(
                        document_id,
                        "actuel",
                        module._(u"Fermeture du document"),
                        module._(u"Opération en cours : Fermeture du document n°%d") % document_id,
                    )
                    publisher.FermerDocument()
                    _publisher_error(publisher, document_id)

                # Étape mail non utilisée par Word/Writer dans le flux historique.
                self._advance()
                self._progress(document_id, "ok", module._(u"Terminé"), None)

            success = True
        except _PublipostageFailure as exc:
            interrupted = self._cancel_event.is_set() or self.stop
            error_message = _as_text(exc)
            if exc.document_id is not None:
                current_document = exc.document_id
        except Exception as exc:
            error_message = _as_text(exc) or exc.__class__.__name__
        finally:
            keep_open = bool(success and job["preview"] and not self._cancel_event.is_set())
            _finalize_publisher(module, publisher, job["software"], keep_open=keep_open)
            _post(
                module,
                page._rc2_worker_finished,
                success,
                interrupted,
                current_document,
                error_message,
            )


def _install_com_lifecycle(module):
    word_class = module.Publipostage_Word
    writer_class = module.Publipostage_Writer_Windows

    original_word_init = word_class.__init__
    original_writer_init = writer_class.__init__
    original_word_quit = word_class.QuitterLogiciel
    original_writer_quit = writer_class.QuitterLogiciel

    def word_init(self, parent):
        original_word_init(self, parent)
        self._rc2_com_initialized = True
        self._rc2_finalized = False
        self._rc2_worker_managed = False
        self.Word = None
        self.doc = None

    def writer_init(self, parent):
        original_writer_init(self, parent)
        self._rc2_com_initialized = True
        self._rc2_finalized = False
        self._rc2_worker_managed = False
        self.objDesktop = None
        self.objDocument = None

    def word_quit(self):
        if getattr(self, "_rc2_worker_managed", False):
            # Les méthodes historiques demandent parfois QuitterLogiciel depuis
            # leur except. Le worker propriétaire effectue l'unique cleanup en
            # finally, après la dernière utilisation du proxy COM.
            return
        return original_word_quit(self)

    def writer_quit(self):
        if getattr(self, "_rc2_worker_managed", False):
            return
        return original_writer_quit(self)

    def word_open(self):
        try:
            dispatch = getattr(module.win32com.client, "DispatchEx", None)
            if dispatch is None:
                dispatch = module.win32com.client.Dispatch
            self.Word = dispatch("Word.Application")
            self.Word.Visible = False
        except Exception as err:
            print("Erreur dans l'ouverture de Word : %s" % err)
            self.erreur = module._(u"Impossible d'ouvrir Word")

    word_class.__init__ = word_init
    writer_class.__init__ = writer_init
    word_class.QuitterLogiciel = word_quit
    writer_class.QuitterLogiciel = writer_quit
    word_class.OuvertureLogiciel = word_open


def _install_page_lifecycle(module):
    page_class = module.Page6
    original_validation = page_class.Validation
    original_continue = page_class.Onbouton_continuer

    def _set_controls_running(self, running):
        wizard = self.GetGrandParent()
        wizard.bouton_annuler.Enable(not running)
        wizard.bouton_retour.Enable(not running)
        wizard.bouton_aide.Enable(not running)
        wizard.EnableCloseButton(not running)
        if running:
            wizard.SetSuiteAction(u"Arrêter", "Arreter_L72.png", role="danger")
        else:
            wizard.bouton_suite.Enable(True)

    def _rc2_progress(self, document_id, state, info, intro=None):
        self.AfficheProgression(document_id, state, info, intro)

    def _rc2_advance(self):
        try:
            self.gauge.SetValue(min(self.x, self.nbreCrans))
        except Exception:
            pass
        self.x += 1

    def _rc2_set_paused(self, paused):
        self.pause = bool(paused)
        self.bouton_continuer.Show(bool(paused))
        self.Layout()

    def _rc2_worker_finished(self, success, interrupted, document_id, error_message):
        thread = getattr(self, "thread", None)
        if _thread_is_alive(thread):
            # CallAfter peut être consommé juste avant le retour effectif de
            # Thread.run(). Ne réactiver la navigation qu'une fois le thread mort.
            module.wx.CallLater(
                25,
                self._rc2_worker_finished,
                success,
                interrupted,
                document_id,
                error_message,
            )
            return

        self._rc2_set_paused(False)
        self.termine = bool(success)
        self.interrompu = bool(interrupted)
        self._rc2_cancel_event = None
        self._rc2_continue_event = None
        _set_controls_running(self, False)
        wizard = self.GetGrandParent()

        if success:
            self.label_intro.SetLabel(module._(u"Le publipostage est terminé."))
            wizard.SetSuiteAction(u"Fermer", "Fermer_L72.png")
        elif interrupted:
            self.label_intro.SetLabel(module._(u"Vous avez interrompu le publipostage ! "))
            wizard.SetSuiteAction(u"Valider", "Valider_L72.png")
        else:
            message = error_message or module._(u"Erreur inconnue pendant le publipostage")
            self.AfficheProgression(
                document_id,
                "erreur",
                module._(u"Erreur : %s") % message,
                module._(u"Erreur : %s") % message,
            )
            wizard.SetSuiteAction(u"Valider", "Valider_L72.png")

    def validation(self):
        if self.choixLogiciel not in (1, 2) or "win" not in module.sys.platform:
            return original_validation(self)

        thread = getattr(self, "thread", None)
        if _thread_is_alive(thread):
            cancel_event = getattr(self, "_rc2_cancel_event", None)
            continue_event = getattr(self, "_rc2_continue_event", None)
            if cancel_event is not None:
                cancel_event.set()
            if continue_event is not None:
                continue_event.set()
            thread.abort()
            self.GetGrandParent().bouton_suite.Enable(False)
            self.label_intro.SetLabel(module._(u"Arrêt du publipostage en cours…"))
            return False

        if self.termine:
            return True

        job = _snapshot_job(module, self)
        self.ctrl_actions.Remplissage()
        self.nbreDocuments = job["count"]
        self.nbreCrans = (self.nbreDocuments * 6) + 3
        self.gauge.SetRange(max(1, self.nbreCrans))
        self.gauge.SetValue(0)
        self.x = 1
        self.pause = False
        self.interrompu = False
        self.label_intro.SetLabel(module._(u"Opération en cours : Ouverture du logiciel de publipostage"))
        self.gauge.SetValue(self.x)
        self.x += 1
        _set_controls_running(self, True)

        cancel_event = threading.Event()
        continue_event = threading.Event()
        self._rc2_cancel_event = cancel_event
        self._rc2_continue_event = continue_event
        self.thread = _PublipostageWorker(module, self, job, cancel_event, continue_event)
        self.thread.start()
        return False

    def continue_handler(self, event):
        if self.choixLogiciel in (1, 2) and "win" in module.sys.platform:
            continue_event = getattr(self, "_rc2_continue_event", None)
            if continue_event is not None:
                self._rc2_set_paused(False)
                continue_event.set()
                return
        return original_continue(self, event)

    page_class._rc2_progress = _rc2_progress
    page_class._rc2_advance = _rc2_advance
    page_class._rc2_set_paused = _rc2_set_paused
    page_class._rc2_worker_finished = _rc2_worker_finished
    page_class.Validation = validation
    page_class.Onbouton_continuer = continue_handler


def install(module):
    """Installe une seule fois le correctif RC2 sur le module historique."""
    if getattr(module, "_RC2_PUBLIPOSTAGE_LIFECYCLE", False):
        return module
    module._RC2_PUBLIPOSTAGE_LIFECYCLE = True
    if "win" in module.sys.platform:
        _install_com_lifecycle(module)
    _install_page_lifecycle(module)
    return module
