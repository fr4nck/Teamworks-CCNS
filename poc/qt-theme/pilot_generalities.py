from __future__ import annotations

from PySide6.QtCore import QThread, QTimer

from generalities_page import GeneralitiesPage
from individual_activity_presenter import IndividualActivityPresenter
from pilot_view import PeopleContractsPilot, _contract_count_text, _initials


class PeopleContractsGeneralitiesPilot(PeopleContractsPilot):
    """Pilote Individus/Contrats avec Généralités et lectures individuelles Qt."""

    CLOSE_WAIT_TIMEOUT_MS = 100

    def __init__(self, adapter, parent=None, *, activity_loader_class=None):
        self._activity_loader_class = activity_loader_class
        self._activity_thread = None
        self._activity_worker = None
        self._activity_loading_person_id = None
        self._activity_pending_person_id = None
        self._activity_selected_person_id = None
        self._people_loader_thread = None
        self._people_loader_worker = None
        self._closing_requested = False
        self._deferred_close_scheduled = False
        self._last_close_wait_timed_out = False
        super().__init__(adapter, parent)
        self.activity_presenter = IndividualActivityPresenter(self.legacy_tabs)

    def _build_general_tab(self):
        self.generalities_page = GeneralitiesPage(self)
        return self.generalities_page

    def is_closing_requested(self) -> bool:
        return self._closing_requested

    def attach_people_loader(self, thread: QThread, worker) -> None:
        """Track the launcher people worker with the same close policy as activity."""
        if self._closing_requested:
            raise RuntimeError("Impossible de démarrer un chargement pendant la fermeture")
        self._people_loader_thread = thread
        self._people_loader_worker = worker
        thread.finished.connect(self._on_people_loader_finished)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

    def _show_empty_detail(self) -> None:
        super()._show_empty_detail()
        page = getattr(self, "generalities_page", None)
        if page is not None:
            page.clear()
        self._activity_selected_person_id = None
        presenter = getattr(self, "activity_presenter", None)
        if presenter is not None:
            presenter.clear()

    def _show_person_from_proxy_row(self, proxy_row: int) -> None:
        if self._closing_requested:
            return
        source_index = self.people_proxy.mapToSource(self.people_proxy.index(proxy_row, 0))
        person = self.people_model.person_at(source_index.row())
        if person is None:
            self._show_empty_detail()
            return

        self.generalities_page.set_person(person)

        contract_key = person.id_historique if person.id_historique is not None else person.id
        self.contracts_model.replace(())
        self.contracts_stack.setCurrentIndex(0)
        self.contracts_model.replace(self.adapter.list_contracts(contract_key))
        contract_count = self.contracts_model.rowCount()
        self.contracts_stack.setCurrentIndex(1 if contract_count else 0)

        historical_id = person.id_historique if person.id_historique is not None else person.id
        self.detail_id.setText(f"{person.contract or 'Aucun contrat en cours'} | ID : {historical_id}")
        self.detail_title.setText(person.name or "—")
        context_parts = [value for value in (person.role, person.site) if value and value != "—"]
        self.detail_context.setText(" · ".join(context_parts) if context_parts else "Adresse / situation : —")
        self.detail_birth.setText(f"Naissance : {person.birth_date or '—'}")
        self.detail_contracts.setText(_contract_count_text(contract_count))
        self.person_avatar.setText(_initials(person.name))
        self.detail_stack.setCurrentIndex(1)

        self._request_activity(historical_id)
        self.statusBar().showMessage(
            f"Lecture seule · {person.name} · {contract_count} contrat(s) · chargement du dossier…"
        )

    def _request_activity(self, person_id) -> None:
        if self._closing_requested:
            return
        self._activity_selected_person_id = person_id
        self.activity_presenter.clear()

        if self._activity_loader_class is None:
            payload = {
                "generalities": self.adapter.get_person_generalities(person_id),
                "scenarios": tuple(self.adapter.list_scenarios(person_id)),
                "trips": tuple(self.adapter.list_trips(person_id)),
                "reimbursements": tuple(self.adapter.list_reimbursements(person_id)),
            }
            self._apply_individual_payload(person_id, payload)
            return

        if self._activity_thread is not None and self._activity_thread.isRunning():
            if self._activity_loading_person_id != person_id:
                self._activity_pending_person_id = person_id
            return
        self._start_activity_load(person_id)

    def _start_activity_load(self, person_id) -> None:
        if self._closing_requested:
            return
        thread = QThread(self)
        worker = self._activity_loader_class(person_id)
        worker.moveToThread(thread)
        self._activity_thread = thread
        self._activity_worker = worker
        self._activity_loading_person_id = person_id
        self._activity_pending_person_id = None

        worker.loaded.connect(self._on_activity_loaded)
        worker.failed.connect(self._on_activity_failed)
        thread.started.connect(worker.run)
        thread.finished.connect(self._on_activity_finished)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _apply_individual_payload(self, person_id, payload) -> None:
        if self._closing_requested:
            return
        if person_id != self._activity_selected_person_id:
            return
        details = payload.get("generalities")
        self.generalities_page.set_details(details)
        if details is not None:
            address_parts = [
                value
                for value in (details.address, details.postcode, details.city)
                if value and value != "—"
            ]
            self.detail_context.setText(
                " · ".join(address_parts) if address_parts else "Adresse / situation : —"
            )
            birth_parts = [
                value
                for value in (details.birth_date, details.birth_city)
                if value and value != "—"
            ]
            self.detail_birth.setText(
                "Naissance : " + (" · ".join(birth_parts) if birth_parts else "—")
            )
        self.activity_presenter.set_payload(payload)

    def _on_activity_loaded(self, person_id, payload) -> None:
        if not self._closing_requested:
            if person_id == self._activity_selected_person_id:
                self._apply_individual_payload(person_id, payload)
                scenarios = len(payload.get("scenarios", ()))
                trips = len(payload.get("trips", ()))
                reimbursements = len(payload.get("reimbursements", ()))
                seconds = float(payload.get("seconds", 0.0))
                self.statusBar().showMessage(
                    "Lecture seule · dossier prêt · "
                    f"{scenarios} scénario(s) · {trips} déplacement(s) · "
                    f"{reimbursements} remboursement(s) · {seconds:.2f}s"
                )
        if self._activity_thread is not None:
            self._activity_thread.quit()

    def _on_activity_failed(self, person_id, details: str) -> None:
        if not self._closing_requested:
            print("[Teamworks Qt POC] Échec lecture du dossier individuel :")
            print(details)
            if person_id == self._activity_selected_person_id:
                self.activity_presenter.clear()
                self.statusBar().showMessage("Lecture seule · échec du chargement du dossier")
        if self._activity_thread is not None:
            self._activity_thread.quit()

    def _on_activity_finished(self) -> None:
        pending = None if self._closing_requested else self._activity_pending_person_id
        self._activity_thread = None
        self._activity_worker = None
        self._activity_loading_person_id = None
        self._activity_pending_person_id = None
        if self._closing_requested:
            self._try_complete_deferred_close()
        elif pending is not None and pending == self._activity_selected_person_id:
            self._start_activity_load(pending)

    def _on_people_loader_finished(self) -> None:
        self._people_loader_thread = None
        self._people_loader_worker = None
        if self._closing_requested:
            self._try_complete_deferred_close()

    def _tracked_background_threads(self):
        return tuple(
            (name, thread)
            for name, thread in (
                ("personnes", self._people_loader_thread),
                ("dossier", self._activity_thread),
            )
            if thread is not None
        )

    def _running_background_threads(self):
        result = []
        for name, thread in self._tracked_background_threads():
            try:
                if thread.isRunning():
                    result.append((name, thread))
            except RuntimeError:
                continue
        return tuple(result)

    def _begin_close(self) -> None:
        if self._closing_requested:
            return
        self._closing_requested = True
        self._activity_pending_person_id = None
        self._activity_selected_person_id = None
        presenter = getattr(self, "activity_presenter", None)
        if presenter is not None:
            presenter.clear()
        self.setEnabled(False)
        self.statusBar().showMessage("Fermeture demandée · attente des lectures en cours…")

    def _request_background_stop(self) -> None:
        for _name, thread in self._running_background_threads():
            thread.quit()

    def stop_background_threads(self, wait_timeout_ms: int | None) -> bool:
        """Request a cooperative Qt-loop stop and optionally wait for DB work.

        A synchronous DB call already executing in worker.run() cannot be interrupted by
        QThread.quit(). A finite timeout therefore returns False instead of permitting
        destruction. Passing None waits until those calls return, for final process
        teardown where keeping the QThread alive is safer than destroying it running.
        """
        self._begin_close()
        threads = self._running_background_threads()
        for _name, thread in threads:
            thread.quit()

        all_stopped = True
        for _name, thread in threads:
            if wait_timeout_ms is None:
                thread.wait()
            elif not thread.wait(wait_timeout_ms):
                all_stopped = False
        return all_stopped

    def _try_complete_deferred_close(self) -> None:
        if not self._closing_requested:
            return
        if self._activity_thread is not None or self._people_loader_thread is not None:
            return
        if self._deferred_close_scheduled:
            return
        self._deferred_close_scheduled = True
        QTimer.singleShot(0, self._finish_deferred_close)

    def _finish_deferred_close(self) -> None:
        self._deferred_close_scheduled = False
        if self._closing_requested and self._activity_thread is None and self._people_loader_thread is None:
            self.close()

    def closeEvent(self, event) -> None:
        self._begin_close()
        tracked = self._tracked_background_threads()
        if tracked:
            self._request_background_stop()
            timed_out = []
            for name, thread in self._running_background_threads():
                if not thread.wait(self.CLOSE_WAIT_TIMEOUT_MS):
                    timed_out.append(name)
            self._last_close_wait_timed_out = bool(timed_out)
            if timed_out:
                self.statusBar().showMessage(
                    "Fermeture différée · lecture synchrone encore active : " + ", ".join(timed_out)
                )
            else:
                self.statusBar().showMessage("Fermeture différée · finalisation des workers…")
            event.ignore()
            QTimer.singleShot(0, self._try_complete_deferred_close)
            return
        super().closeEvent(event)
