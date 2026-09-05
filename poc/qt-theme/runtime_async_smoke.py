from __future__ import annotations

import faulthandler
import os
import sys
import time
import traceback
from types import SimpleNamespace

faulthandler.enable(all_threads=True)

_NATIVE_WINDOWS_REQUIRED = (
    os.environ.get("TEAMWORKS_QT_NATIVE_WINDOWS_REQUIRED", "").strip() == "1"
)
if sys.platform != "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication

from data_adapter import PersonGeneralitiesView, PersonView
from pilot_generalities import PeopleContractsGeneralitiesPilot


def _stage(label: str) -> None:
    print(f"[Teamworks Qt runtime] stage={label}", flush=True)


class _FakeAdapter:
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
        return ()

    def get_person_generalities(self, person_id):
        return None

    def list_scenarios(self, person_id):
        return ()

    def list_trips(self, person_id):
        return ()

    def list_reimbursements(self, person_id):
        return ()


class _FakeActivityWorker(QObject):
    loaded = Signal(object, object)
    failed = Signal(object, str)
    delays_ms: dict[int, int] = {}

    def __init__(self, person_id: int):
        super().__init__()
        self.person_id = int(person_id)
        self._timer = None

    @Slot()
    def run(self) -> None:
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._emit_payload)
        self._timer.start(self.delays_ms.get(self.person_id, 10))

    @Slot()
    def _emit_payload(self) -> None:
        label = {1: "A", 2: "B", 3: "C"}[self.person_id]
        self.loaded.emit(
            self.person_id,
            {
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
            },
        )


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


def _process_until(app: QApplication, predicate, *, timeout: float = 3.0, forbidden=()) -> None:
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        app.processEvents()
        current = _questionnaire_text(_process_until.window)
        if current in forbidden:
            raise AssertionError(f"donnee obsolete reapparue: {current}")
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError("timeout du smoke runtime Qt")


def _wait(window, predicate, *, timeout: float = 3.0, forbidden=()) -> None:
    _process_until.window = window
    _process_until(_app(), predicate, timeout=timeout, forbidden=forbidden)


def _select(window, row: int) -> None:
    window.people_table.selectRow(row)
    _app().processEvents()


def _assert_activity_rows(window, expected: int) -> None:
    assert window.legacy_tabs.questionnaire_page.model.rowCount() == expected
    assert window.legacy_tabs.scenarios_page.model.rowCount() == expected
    assert window.legacy_tabs.expenses_page.trip_model.rowCount() == expected
    assert window.legacy_tabs.expenses_page.reimbursement_model.rowCount() == expected


def _thread_stopped_or_deleted(thread) -> bool:
    try:
        return not thread.isRunning()
    except RuntimeError:
        return True


def _new_window(delays: dict[int, int]) -> PeopleContractsGeneralitiesPilot:
    _FakeActivityWorker.delays_ms = dict(delays)
    window = PeopleContractsGeneralitiesPilot(
        _FakeAdapter(),
        activity_loader_class=_FakeActivityWorker,
    )
    window.show()
    _app().processEvents()
    return window


def run_smoke() -> None:
    app = _app()
    platform_name = app.platformName()
    _stage(f"platform-{platform_name}")
    if _NATIVE_WINDOWS_REQUIRED:
        assert sys.platform == "win32", "qualification native Windows demandee hors Windows"
        assert platform_name.lower() == "windows", (
            "plugin Qt Windows natif attendu, "
            f"plateforme active: {platform_name!r}"
        )

    _stage("clear-a-b-start")
    window = _new_window({1: 10, 2: 120, 3: 10})
    try:
        expected_tabs = [
            "Generalites",
            "Questionnaire",
            "Qualifications",
            "Contrats",
            "Presences",
            "Scenarios",
            "Frais",
            "Recrutement",
        ]
        actual_tabs = [window.tabs.tabText(index) for index in range(window.tabs.count())]
        normalized_tabs = [
            text.replace("é", "e").replace("è", "e").replace("É", "E")
            for text in actual_tabs
        ]
        assert normalized_tabs == expected_tabs
        for index in range(window.tabs.count()):
            window.tabs.setCurrentIndex(index)
            app.processEvents()
            assert window.tabs.currentIndex() == index

        _select(window, 0)
        _wait(window, lambda: _questionnaire_text(window) == "Question A")
        _assert_activity_rows(window, 1)
        assert window.generalities_page.address.toPlainText() == "Adresse A"

        _select(window, 1)
        _assert_activity_rows(window, 0)
        assert window.generalities_page.address.toPlainText() == ""
        assert window.generalities_page.memo.toPlainText() == ""
        assert window.generalities_page.last_name.text() == "NomB"
        _wait(window, lambda: _questionnaire_text(window) == "Question B")
        _assert_activity_rows(window, 1)
        assert window.generalities_page.address.toPlainText() == "Adresse B"
        _wait(window, lambda: window._activity_thread is None)
    finally:
        window.close()
        app.processEvents()
    _stage("clear-a-b-ok")

    _stage("stale-a-b-c-start")
    window = _new_window({1: 140, 2: 10, 3: 10})
    try:
        _select(window, 0)
        _wait(window, lambda: window._activity_thread is not None and window._activity_thread.isRunning())
        _select(window, 1)
        _assert_activity_rows(window, 0)
        _wait(
            window,
            lambda: _questionnaire_text(window) == "Question B",
            forbidden=("Question A",),
        )
        _wait(window, lambda: window._activity_thread is None)

        _select(window, 0)
        _wait(window, lambda: window._activity_thread is not None and window._activity_thread.isRunning())
        _select(window, 1)
        _select(window, 2)
        _assert_activity_rows(window, 0)
        _wait(
            window,
            lambda: _questionnaire_text(window) == "Question C",
            forbidden=("Question A", "Question B"),
        )
        _wait(window, lambda: window._activity_thread is None)
    finally:
        window.close()
        app.processEvents()
    _stage("stale-a-b-c-ok")

    _stage("close-timer-start")
    window = _new_window({1: 500})
    _select(window, 0)
    _wait(window, lambda: window._activity_thread is not None and window._activity_thread.isRunning())
    thread = window._activity_thread
    window.close()
    app.processEvents()
    assert window.is_closing_requested()
    _assert_activity_rows(window, 0)
    _wait(window, lambda: window._activity_thread is None)
    assert _thread_stopped_or_deleted(thread)
    _wait(window, lambda: not window.isVisible())
    _stage("close-timer-ok")

    print(
        f"[Teamworks Qt runtime] OK - plateforme={platform_name} - "
        "8 onglets, clear A->B, rejet stale A, A->B->C, fermeture thread",
        flush=True,
    )


if __name__ == "__main__":
    try:
        run_smoke()
    except BaseException:
        traceback.print_exc()
        raise
