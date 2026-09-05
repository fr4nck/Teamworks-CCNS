from __future__ import annotations

import os
import sys
import time
import traceback

from PySide6.QtCore import QEventLoop, QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication

from pilot_generalities import PeopleContractsGeneralitiesPilot
from runtime_async_smoke import (
    _ControlledBlockingWorker,
    _FakeAdapter,
    _payload,
    _questionnaire_text,
)


class _TimerWorker(QObject):
    """Reproduction exacte du faux worker QTimer du smoke historique."""

    loaded = Signal(object, object)
    failed = Signal(object, str)
    delays_ms: dict[int, int] = {1: 10, 2: 120, 3: 10}

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
        self.loaded.emit(self.person_id, _payload(self.person_id))


def _app() -> QApplication:
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setQuitOnLastWindowClosed(False)
    return app


def _thread_none(window) -> bool:
    return window._activity_thread is None


def _thread_state(window) -> str:
    thread = window._activity_thread
    if thread is None:
        return "none"
    try:
        return f"running={thread.isRunning()} finished={thread.isFinished()}"
    except RuntimeError:
        return "deleted"


def _wait_poll(window, predicate, *, timeout: float = 3.0) -> None:
    deadline = time.perf_counter() + timeout
    app = _app()
    while time.perf_counter() < deadline:
        app.processEvents()
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError(f"poll timeout; thread={_thread_state(window)}")


def _wait_loop(window, predicate, *, timeout_ms: int = 3000) -> None:
    loop = QEventLoop()
    poll = QTimer()
    poll.setInterval(5)
    timeout = QTimer()
    timeout.setSingleShot(True)
    result = {"ok": False}

    def check() -> None:
        if predicate():
            result["ok"] = True
            loop.quit()

    poll.timeout.connect(check)
    timeout.timeout.connect(loop.quit)
    poll.start()
    timeout.start(timeout_ms)
    QTimer.singleShot(0, check)
    loop.exec()
    poll.stop()
    timeout.stop()
    if not result["ok"]:
        raise AssertionError(f"eventloop timeout; thread={_thread_state(window)}")


def _navigate_tabs_poll(window) -> None:
    for index in range(window.tabs.count()):
        window.tabs.setCurrentIndex(index)
        _app().processEvents()
        assert window.tabs.currentIndex() == index


def _navigate_tabs_loop(window) -> None:
    for index in range(window.tabs.count()):
        window.tabs.setCurrentIndex(index)
        _wait_loop(window, lambda index=index: window.tabs.currentIndex() == index)


def _new_window(worker_class):
    if worker_class is _ControlledBlockingWorker:
        _ControlledBlockingWorker.reset()
    window = PeopleContractsGeneralitiesPilot(
        _FakeAdapter(),
        activity_loader_class=worker_class,
    )
    window.show()
    assert window.isVisible(), "window must be visible"
    return window


def _finish_close_poll(window) -> None:
    if not _thread_none(window):
        _wait_poll(window, lambda: _thread_none(window))
    window.close()
    _wait_poll(window, lambda: not window.isVisible())


def _finish_close_loop(window) -> None:
    if not _thread_none(window):
        _wait_loop(window, lambda: _thread_none(window))
    window.close()
    _wait_loop(window, lambda: not window.isVisible())


def _timer_poll(*, tabs: bool, wait_full_a: bool) -> None:
    window = _new_window(_TimerWorker)
    _app().processEvents()
    try:
        if tabs:
            _navigate_tabs_poll(window)
        window.people_table.selectRow(0)
        _app().processEvents()
        _wait_poll(window, lambda: _questionnaire_text(window) == "Question A")
        print(
            f"PROBE after-A payload tabs={tabs} wait_full_a={wait_full_a} thread={_thread_state(window)}",
            flush=True,
        )
        if wait_full_a:
            _wait_poll(window, lambda: _thread_none(window))
            print("PROBE after-A thread-finished", flush=True)
        window.people_table.selectRow(1)
        _app().processEvents()
        print(f"PROBE after-select-B thread={_thread_state(window)}", flush=True)
        _wait_poll(window, lambda: _questionnaire_text(window) == "Question B")
        _wait_poll(window, lambda: _thread_none(window))
        print("PROBE B-visible-and-thread-finished", flush=True)
    finally:
        _finish_close_poll(window)


def _timer_loop(*, tabs: bool, wait_full_a: bool) -> None:
    window = _new_window(_TimerWorker)
    try:
        if tabs:
            _navigate_tabs_loop(window)
        window.people_table.selectRow(0)
        _wait_loop(window, lambda: _questionnaire_text(window) == "Question A")
        print(
            f"PROBE loop after-A payload tabs={tabs} wait_full_a={wait_full_a} thread={_thread_state(window)}",
            flush=True,
        )
        if wait_full_a:
            _wait_loop(window, lambda: _thread_none(window))
        window.people_table.selectRow(1)
        _wait_loop(window, lambda: _questionnaire_text(window) == "Question B")
        _wait_loop(window, lambda: _thread_none(window))
        print("PROBE loop B-visible-and-thread-finished", flush=True)
    finally:
        _finish_close_loop(window)


def _blocking_poll(*, tabs: bool) -> None:
    window = _new_window(_ControlledBlockingWorker)
    _app().processEvents()
    try:
        if tabs:
            _navigate_tabs_poll(window)
        window.people_table.selectRow(0)
        _app().processEvents()
        _wait_poll(window, lambda: _ControlledBlockingWorker.started(1))
        _ControlledBlockingWorker.release(1)
        _wait_poll(window, lambda: _questionnaire_text(window) == "Question A")
        print(f"PROBE blocking after-A payload thread={_thread_state(window)}", flush=True)
        window.people_table.selectRow(1)
        _app().processEvents()
        _wait_poll(window, lambda: _ControlledBlockingWorker.started(2))
        _ControlledBlockingWorker.release(2)
        _wait_poll(window, lambda: _questionnaire_text(window) == "Question B")
        _wait_poll(window, lambda: _thread_none(window))
        print("PROBE blocking B-visible-and-thread-finished", flush=True)
    finally:
        _ControlledBlockingWorker.release_all()
        _finish_close_poll(window)


def run(case: str) -> None:
    if sys.platform != "win32":
        raise AssertionError("probe qwindows requires Windows")
    if os.environ.get("QT_QPA_PLATFORM"):
        raise AssertionError(f"QT_QPA_PLATFORM must be unset, got {os.environ['QT_QPA_PLATFORM']!r}")
    platform = _app().platformName()
    print(f"PROBE case={case} platform={platform}", flush=True)
    assert platform.lower() == "windows", platform

    cases = {
        "timer-poll-race": lambda: _timer_poll(tabs=False, wait_full_a=False),
        "timer-poll-race-tabs": lambda: _timer_poll(tabs=True, wait_full_a=False),
        "timer-poll-finished": lambda: _timer_poll(tabs=False, wait_full_a=True),
        "timer-poll-finished-tabs": lambda: _timer_poll(tabs=True, wait_full_a=True),
        "timer-loop-race": lambda: _timer_loop(tabs=False, wait_full_a=False),
        "timer-loop-race-tabs": lambda: _timer_loop(tabs=True, wait_full_a=False),
        "timer-loop-finished": lambda: _timer_loop(tabs=False, wait_full_a=True),
        "blocking-poll-race-tabs": lambda: _blocking_poll(tabs=True),
    }
    cases[case]()
    print(f"PROBE PASS case={case}", flush=True)


if __name__ == "__main__":
    try:
        run(sys.argv[1])
    except BaseException:
        traceback.print_exc()
        raise
