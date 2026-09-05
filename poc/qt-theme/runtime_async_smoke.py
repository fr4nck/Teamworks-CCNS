from __future__ import annotations

import faulthandler
import os
import sys
import threading
import time
import traceback
from types import SimpleNamespace

faulthandler.enable(all_threads=True)

_NATIVE_WINDOWS_REQUIRED = (
    os.environ.get("TEAMWORKS_QT_NATIVE_WINDOWS_REQUIRED", "").strip() == "1"
)
if sys.platform != "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication

from data_adapter import ContractView, PersonGeneralitiesView, PersonView
from pilot_generalities import PeopleContractsGeneralitiesPilot


_EXPECTED_TABS = (
    "Généralités",
    "Questionnaire",
    "Qualifications",
    "Contrats",
    "Présences",
    "Scénarios",
    "Frais",
    "Recrutement",
)


def _stage(label: str) -> None:
    print(f"[Teamworks Qt runtime] stage={label}", flush=True)


def _payload(person_id: int) -> dict[str, object]:
    label = {1: "A", 2: "B", 3: "C"}[int(person_id)]
    return {
        "generalities": PersonGeneralitiesView(
            civility="",
            maiden_name="",
            last_name=f"Nom{label}",
            first_name=f"Prenom{label}",
            birth_date="01/01/2000",
            birth_country="",
            birth_postcode="",
            birth_city=f"Ville {label}",
            nationality="",
            social_situation="",
            address=f"Adresse {label}",
            postcode="",
            city=f"Ville {label}",
            memo=f"Memo {label}",
            coordinates=(),
        ),
        "questionnaire": (
            SimpleNamespace(question=f"Question {label}", answer=f"Reponse {label}"),
        ),
        "scenarios": (
            SimpleNamespace(name=f"Scenario {label}", period="2026", description=""),
        ),
        "trips": (
            SimpleNamespace(
                number="1",
                date="01/09/2026",
                purpose=f"Objet {label}",
                route="A -> B",
                distance="1 Km",
                tariff="1 EUR/km",
                amount="1 EUR",
                reimbursement="",
            ),
        ),
        "reimbursements": (
            SimpleNamespace(
                number="1",
                date="01/09/2026",
                amount="1 EUR",
                attached_trips="1",
            ),
        ),
        "seconds": 0.01,
    }


class _FakeAdapter:
    def __init__(self) -> None:
        self.contract_probe = None

    def list_people(self):
        return tuple(
            PersonView(
                id="",
                id_historique=person_id,
                name=f"Personne {label}",
                first_name=f"Prenom{label}",
                last_name=f"Nom{label}",
                birth_date="01/01/2000",
                role="",
                classification="",
                contract="",
                weekly_hours="",
                status="",
                site="",
                medical="",
                mutual="",
            )
            for person_id, label in ((1, "A"), (2, "B"), (3, "C"))
        )

    def list_contracts(self, person_id):
        numeric_id = int(person_id)
        if self.contract_probe is not None:
            self.contract_probe(numeric_id)
        label = {1: "A", 2: "B", 3: "C"}[numeric_id]
        return (
            ContractView(
                kind=f"Contrat {label}",
                start="01/09/2026",
                end="31/08/2027",
                classification="",
                duration="",
                status="Lecture seule",
            ),
        )

    def get_person_generalities(self, person_id):
        return _payload(int(person_id))["generalities"]

    def list_scenarios(self, person_id):
        return _payload(int(person_id))["scenarios"]

    def list_trips(self, person_id):
        return _payload(int(person_id))["trips"]

    def list_reimbursements(self, person_id):
        return _payload(int(person_id))["reimbursements"]


class _ControlledBlockingWorker(QObject):
    """Worker de smoke calqué sur le run() bloquant du loader de production.

    Les threading.Event donnent uniquement au scénario de test le contrôle du moment
    où la lecture bloquante se termine. Aucun QTimer ne remplace le worker métier.
    """

    loaded = Signal(object, object)
    failed = Signal(object, str)
    _started_events: dict[int, threading.Event] = {}
    _release_events: dict[int, threading.Event] = {}

    def __init__(self, person_id: int):
        super().__init__()
        self.person_id = int(person_id)
        type(self)._started_events[self.person_id] = threading.Event()
        type(self)._release_events[self.person_id] = threading.Event()

    @classmethod
    def reset(cls) -> None:
        cls._started_events = {}
        cls._release_events = {}

    @classmethod
    def started(cls, person_id: int) -> bool:
        event = cls._started_events.get(int(person_id))
        return bool(event is not None and event.is_set())

    @classmethod
    def release(cls, person_id: int) -> None:
        event = cls._release_events.get(int(person_id))
        if event is None:
            raise AssertionError(f"worker {person_id} non construit")
        event.set()

    @classmethod
    def release_all(cls) -> None:
        for event in tuple(cls._release_events.values()):
            event.set()

    @Slot()
    def run(self) -> None:
        type(self)._started_events[self.person_id].set()
        if not type(self)._release_events[self.person_id].wait(5.0):
            self.failed.emit(self.person_id, "timeout du worker bloquant de smoke")
            return
        self.loaded.emit(self.person_id, _payload(self.person_id))


def _app() -> QApplication:
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setQuitOnLastWindowClosed(False)
    return app


def _questionnaire_text(window) -> str | None:
    model = window.legacy_tabs.questionnaire_page.model
    if model.rowCount() == 0:
        return None
    item = model.item(0, 0)
    return item.text() if item is not None else None


def _activity_rows(window) -> tuple[int, int, int, int]:
    return (
        window.legacy_tabs.questionnaire_page.model.rowCount(),
        window.legacy_tabs.scenarios_page.model.rowCount(),
        window.legacy_tabs.expenses_page.trip_model.rowCount(),
        window.legacy_tabs.expenses_page.reimbursement_model.rowCount(),
    )


def _assert_activity_clear(window) -> None:
    assert _activity_rows(window) == (0, 0, 0, 0), _activity_rows(window)


class _Scenario:
    def __init__(self, name: str):
        _ControlledBlockingWorker.reset()
        self.name = name
        self.adapter = _FakeAdapter()
        self.window = PeopleContractsGeneralitiesPilot(
            self.adapter,
            activity_loader_class=_ControlledBlockingWorker,
        )
        self.contract_checks: list[int] = []
        self.adapter.contract_probe = self._assert_contract_clear_before_read
        self.window.show()
        assert self.window.isVisible(), "la fenêtre Qt doit être réellement affichée"

        self.loop = QEventLoop()
        self.poll_timer = QTimer()
        self.poll_timer.setSingleShot(True)
        self.poll_timer.timeout.connect(self._poll)
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(
            lambda: self.fail(AssertionError(f"timeout global du scénario {self.name}"))
        )
        self.failure: BaseException | None = None
        self._predicate = None
        self._on_success = None
        self._label = ""
        self._deadline = 0.0
        self._forbidden: tuple[str, ...] = ()

    def _assert_contract_clear_before_read(self, person_id: int) -> None:
        rows = self.window.contracts_model.rowCount()
        assert rows == 0, (
            "Contrats doit être vidé avant la lecture du salarié suivant; "
            f"rows={rows}, personne={person_id}"
        )
        self.contract_checks.append(int(person_id))

    def guard(self, callback):
        def wrapped():
            if self.failure is not None:
                return
            try:
                callback()
            except BaseException as exc:
                self.fail(exc)

        return wrapped

    def fail(self, exc: BaseException) -> None:
        if self.failure is not None:
            return
        self.failure = exc
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        _ControlledBlockingWorker.release_all()
        self.poll_timer.stop()
        self.timeout_timer.stop()
        self.loop.quit()

    def _assert_no_forbidden_payload(self) -> None:
        question = _questionnaire_text(self.window)
        address = self.window.generalities_page.address.toPlainText()
        for label in self._forbidden:
            assert question != f"Question {label}", f"payload stale {label} visible"
            assert address != f"Adresse {label}", f"généralités stale {label} visibles"

    def wait_for(
        self,
        predicate,
        on_success,
        label: str,
        *,
        forbidden: tuple[str, ...] = (),
        timeout: float = 3.0,
    ) -> None:
        self._predicate = predicate
        self._on_success = on_success
        self._label = label
        self._deadline = time.perf_counter() + timeout
        self._forbidden = forbidden
        self.poll_timer.start(0)

    @Slot()
    def _poll(self) -> None:
        if self.failure is not None or self._predicate is None:
            return
        try:
            self._assert_no_forbidden_payload()
            if self._predicate():
                callback = self._on_success
                self._predicate = None
                self._on_success = None
                if callback is not None:
                    self.guard(callback)()
                return
            if time.perf_counter() >= self._deadline:
                raise AssertionError(f"timeout: {self._label}")
        except BaseException as exc:
            self.fail(exc)
            return
        self.poll_timer.start(5)

    def visit_tabs(self, on_done, index: int = 0) -> None:
        if index == 0:
            actual = tuple(
                self.window.tabs.tabText(i) for i in range(self.window.tabs.count())
            )
            assert actual == _EXPECTED_TABS, actual
        if index >= self.window.tabs.count():
            on_done()
            return
        self.window.tabs.setCurrentIndex(index)
        assert self.window.tabs.currentIndex() == index
        QTimer.singleShot(0, self.guard(lambda: self.visit_tabs(on_done, index + 1)))

    def finish_window(self) -> None:
        self.window.close()
        self.wait_for(
            lambda: not self.window.isVisible() and self.window._activity_thread is None,
            self.loop.quit,
            "fermeture fenêtre",
            timeout=4.0,
        )

    def run(self, start) -> None:
        QTimer.singleShot(0, self.guard(start))
        self.timeout_timer.start(8000)
        self.loop.exec()
        self.poll_timer.stop()
        self.timeout_timer.stop()
        _ControlledBlockingWorker.release_all()
        if self.failure is not None:
            raise self.failure


def _run_a_b_active() -> None:
    scenario = _Scenario("A->B actif")
    window = scenario.window

    def after_tabs() -> None:
        window.people_table.selectRow(0)
        assert window.contracts_model.rowCount() == 1
        scenario.wait_for(
            lambda: _ControlledBlockingWorker.started(1),
            select_b,
            "worker A actif",
        )

    def select_b() -> None:
        assert window._activity_loading_person_id == 1
        window.people_table.selectRow(1)
        assert scenario.contract_checks == [1, 2]
        assert window.contracts_model.rowCount() == 1
        _assert_activity_clear(window)
        assert window.generalities_page.address.toPlainText() == ""
        assert window._activity_selected_person_id == 2
        assert window._activity_pending_person_id == 2
        _ControlledBlockingWorker.release(1)
        scenario.wait_for(
            lambda: _ControlledBlockingWorker.started(2),
            release_b,
            "worker B après fin de A",
            forbidden=("A",),
        )

    def release_b() -> None:
        _ControlledBlockingWorker.release(2)
        scenario.wait_for(
            lambda: (
                _questionnaire_text(window) == "Question B"
                and window._activity_thread is None
            ),
            verify_b,
            "B final",
            forbidden=("A",),
        )

    def verify_b() -> None:
        assert window.generalities_page.address.toPlainText() == "Adresse B"
        assert _activity_rows(window) == (1, 1, 1, 1)
        scenario.finish_window()

    scenario.run(lambda: scenario.visit_tabs(after_tabs))


def _run_a_b_c_active() -> None:
    scenario = _Scenario("A->B->C actif")
    window = scenario.window

    def start() -> None:
        window.people_table.selectRow(0)
        assert window.contracts_model.rowCount() == 1
        scenario.wait_for(
            lambda: _ControlledBlockingWorker.started(1),
            select_b_c,
            "worker A actif",
        )

    def select_b_c() -> None:
        window.people_table.selectRow(1)
        window.people_table.selectRow(2)
        assert scenario.contract_checks == [1, 2, 3]
        _assert_activity_clear(window)
        assert window.generalities_page.address.toPlainText() == ""
        assert window._activity_selected_person_id == 3
        assert window._activity_pending_person_id == 3
        _ControlledBlockingWorker.release(1)
        scenario.wait_for(
            lambda: _ControlledBlockingWorker.started(3),
            release_c,
            "worker C après fin de A",
            forbidden=("A", "B"),
        )

    def release_c() -> None:
        assert not _ControlledBlockingWorker.started(2), "B ne doit jamais démarrer"
        _ControlledBlockingWorker.release(3)
        scenario.wait_for(
            lambda: (
                _questionnaire_text(window) == "Question C"
                and window._activity_thread is None
            ),
            verify_c,
            "C final",
            forbidden=("A", "B"),
        )

    def verify_c() -> None:
        assert window.generalities_page.address.toPlainText() == "Adresse C"
        assert _activity_rows(window) == (1, 1, 1, 1)
        scenario.finish_window()

    scenario.run(start)


def _run_close_active() -> None:
    scenario = _Scenario("fermeture worker actif")
    window = scenario.window
    lifecycle = {
        "finished": False,
        "destroyed": False,
        "destroyed_before_finished": False,
    }

    def start() -> None:
        window.people_table.selectRow(0)
        scenario.wait_for(
            lambda: _ControlledBlockingWorker.started(1),
            request_close,
            "worker A actif avant fermeture",
        )

    def request_close() -> None:
        thread = window._activity_thread
        assert thread is not None and thread.isRunning()

        def on_finished() -> None:
            lifecycle["finished"] = True

        def on_destroyed(*_args) -> None:
            lifecycle["destroyed_before_finished"] = not lifecycle["finished"]
            lifecycle["destroyed"] = True

        thread.finished.connect(on_finished)
        thread.destroyed.connect(on_destroyed)
        result = window.close()
        assert result is False, "closeEvent doit être refusé tant que le worker bloque"
        assert window.isVisible()
        assert window.is_closing_requested()
        assert window._last_close_wait_timed_out
        assert thread.isRunning()
        _assert_activity_clear(window)
        assert _questionnaire_text(window) is None
        _ControlledBlockingWorker.release(1)
        scenario.wait_for(
            lambda: (
                lifecycle["finished"]
                and lifecycle["destroyed"]
                and window._activity_thread is None
                and not window.isVisible()
            ),
            verify_close,
            "fermeture différée complète",
            forbidden=("A",),
            timeout=4.0,
        )

    def verify_close() -> None:
        assert not lifecycle["destroyed_before_finished"], (
            "un QThread ne doit jamais être détruit avant son signal finished"
        )
        assert _questionnaire_text(window) is None, (
            "aucun payload tardif ne doit être appliqué pendant la fermeture"
        )
        scenario.loop.quit()

    scenario.run(start)


def run_smoke() -> None:
    app = _app()
    platform_name = app.platformName()
    if _NATIVE_WINDOWS_REQUIRED:
        assert sys.platform == "win32", "qualification native Windows demandée hors Windows"
        assert platform_name.lower() == "windows", (
            "plugin Qt Windows natif attendu, "
            f"plateforme active: {platform_name!r}"
        )

    _stage(f"platform-{platform_name}")
    _stage("a-b-active")
    _run_a_b_active()
    _stage("a-b-c-active")
    _run_a_b_c_active()
    _stage("close-active")
    _run_close_active()

    print(
        "[Teamworks Qt runtime] OK - "
        f"plateforme={platform_name} - 8 onglets - "
        "A->B actif sans stale - A->B->C actif final C - "
        "clear immédiat - fermeture différée sûre",
        flush=True,
    )


if __name__ == "__main__":
    try:
        run_smoke()
    except Exception:
        traceback.print_exc()
        raise
