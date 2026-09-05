from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

POC = Path(__file__).resolve().parents[1] / "poc" / "qt-theme"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

from PySide6.QtCore import QObject, Signal, Slot  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import launcher as launcher_module  # noqa: E402
from data_adapter import PersonView  # noqa: E402
from pilot_generalities import PeopleContractsGeneralitiesPilot  # noqa: E402


_APP: QApplication | None = None


class _Adapter:
    def list_people(self):
        return (
            PersonView(
                id="",
                id_historique=1,
                name="Personne A",
                first_name="A",
                last_name="Personne",
                birth_date="",
                role="",
                classification="",
                contract="",
                weekly_hours="",
                status="",
                site="",
                medical="",
                mutual="",
            ),
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


class _BlockingActivityWorker(QObject):
    loaded = Signal(object, object)
    failed = Signal(object, str)
    started = threading.Event()
    release = threading.Event()

    def __init__(self, person_id):
        super().__init__()
        self.person_id = person_id

    @Slot()
    def run(self) -> None:
        type(self).started.set()
        if not type(self).release.wait(5.0):
            self.failed.emit(self.person_id, "blocking worker timeout")
            return
        self.loaded.emit(
            self.person_id,
            {
                "generalities": None,
                "questionnaire": (
                    SimpleNamespace(question="Late question", answer="Late answer"),
                ),
                "scenarios": (),
                "trips": (),
                "reimbursements": (),
                "seconds": 0.0,
            },
        )


class _BlockingPeopleWorker(QObject):
    loaded = Signal(object, object)
    failed = Signal(str)
    started = threading.Event()
    release = threading.Event()

    @Slot()
    def run(self) -> None:
        type(self).started.set()
        if not type(self).release.wait(5.0):
            self.failed.emit("blocking worker timeout")
            return
        self.loaded.emit(
            (
                PersonView(
                    id="",
                    id_historique=2,
                    name="Late Person",
                    first_name="Late",
                    last_name="Person",
                    birth_date="",
                    role="",
                    classification="",
                    contract="",
                    weekly_hours="",
                    status="",
                    site="",
                    medical="",
                    mutual="",
                ),
            ),
            {},
        )


def _app() -> QApplication:
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication(sys.argv[:1])
    return _APP


def _process_until(predicate, timeout: float = 2.0) -> None:
    app = _app()
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        app.processEvents()
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError("timeout waiting for Qt state")


def _drain_without_masking_failure(finished: threading.Event, *, timeout: float = 6.0) -> None:
    deadline = time.perf_counter() + timeout
    app = _app()
    while not finished.is_set() and time.perf_counter() < deadline:
        app.processEvents()
        time.sleep(0.005)
    app.processEvents()


def _new_window(*, activity_loader_class=None):
    app = _app()
    window = PeopleContractsGeneralitiesPilot(
        _Adapter(),
        activity_loader_class=activity_loader_class,
    )
    window.CLOSE_WAIT_TIMEOUT_MS = 30
    window.show()
    app.processEvents()
    return window


def test_activity_close_is_deferred_until_blocking_worker_finishes() -> None:
    _BlockingActivityWorker.started.clear()
    _BlockingActivityWorker.release.clear()

    window = _new_window(activity_loader_class=_BlockingActivityWorker)
    window.people_table.selectRow(0)
    _process_until(lambda: _BlockingActivityWorker.started.is_set())
    print("activity:A worker blocking", flush=True)

    thread = window._activity_thread
    worker = window._activity_worker
    finished = threading.Event()
    assert thread is not None and thread.isRunning()
    thread.finished.connect(finished.set)
    assert worker is not None
    assert thread.parent() is window
    assert window.legacy_tabs.questionnaire_page.model.rowCount() == 0

    try:
        started = time.perf_counter()
        close_result = window.close()
        wait_elapsed = time.perf_counter() - started
        print(
            "activity:B/C/D "
            f"close_result={close_result!r} visible={window.isVisible()} "
            f"closing={window.is_closing_requested()} timed_out={window._last_close_wait_timed_out} "
            f"elapsed={wait_elapsed:.3f}s running={thread.isRunning()} "
            f"owned={thread.parent() is window}",
            flush=True,
        )

        # A/B/C/D: the native QThread.wait(30) path expires while run() is genuinely
        # blocked, and the still-running thread remains owned by the live window.
        assert window.isVisible() is True
        assert window.is_closing_requested() is True
        assert window._last_close_wait_timed_out is True
        assert wait_elapsed < 0.5
        assert thread.isRunning() is True
        assert thread.parent() is window
        assert window._activity_thread is thread
        assert window._activity_worker is worker
        print("activity:C/D native wait expired, ownership retained", flush=True)

        _BlockingActivityWorker.release.set()

        # E/F/H: after run() returns, the native QThread emits finished, the owner
        # clears its references, and only then does the deferred close complete.
        _process_until(finished.is_set)
        _process_until(lambda: window._activity_thread is None)
        _process_until(lambda: window._activity_worker is None)
        _process_until(lambda: not window.isVisible())
        print("activity:E/F/H QThread finished, refs cleared, window closed", flush=True)

        # G: the payload emitted after close was requested must never reach the UI.
        assert window.legacy_tabs.questionnaire_page.model.rowCount() == 0
        print("activity:G late payload ignored; QThread finished before final close", flush=True)
    finally:
        _BlockingActivityWorker.release.set()
        _drain_without_masking_failure(finished)


def test_people_close_is_deferred_and_late_people_are_ignored() -> None:
    _BlockingPeopleWorker.started.clear()
    _BlockingPeopleWorker.release.clear()

    window = _new_window()
    thread = launcher_module.start_people_loader(
        window,
        _BlockingPeopleWorker,
        total_to_show_seconds=0.0,
    )
    _process_until(lambda: _BlockingPeopleWorker.started.is_set())
    print("people:A worker blocking", flush=True)

    worker = window._people_loader_worker
    finished = threading.Event()
    thread.finished.connect(finished.set)
    assert thread.isRunning()
    assert worker is not None
    assert thread.parent() is window
    assert window.people_model.person_at(0).name == "Personne A"

    try:
        started = time.perf_counter()
        close_result = window.close()
        wait_elapsed = time.perf_counter() - started
        print(
            "people:B/C/D "
            f"close_result={close_result!r} visible={window.isVisible()} "
            f"closing={window.is_closing_requested()} timed_out={window._last_close_wait_timed_out} "
            f"elapsed={wait_elapsed:.3f}s running={thread.isRunning()} "
            f"owned={thread.parent() is window}",
            flush=True,
        )

        assert window.isVisible() is True
        assert window.is_closing_requested() is True
        assert window._last_close_wait_timed_out is True
        assert wait_elapsed < 0.5
        assert thread.isRunning() is True
        assert thread.parent() is window
        assert window._people_loader_thread is thread
        assert window._people_loader_worker is worker
        print("people:C/D native wait expired, ownership retained", flush=True)

        _BlockingPeopleWorker.release.set()

        _process_until(finished.is_set)
        _process_until(lambda: window._people_loader_thread is None)
        _process_until(lambda: window._people_loader_worker is None)
        _process_until(lambda: not window.isVisible())
        print("people:E/F/H QThread finished, refs cleared, window closed", flush=True)

        # The late loader result is discarded because shutdown has started.
        assert window.people_model.rowCount() == 1
        assert window.people_model.person_at(0).name == "Personne A"
        print("people:G late payload ignored; QThread finished before final close", flush=True)
    finally:
        _BlockingPeopleWorker.release.set()
        _drain_without_masking_failure(finished)
