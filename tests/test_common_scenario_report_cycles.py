from __future__ import annotations

import threading

import pytest

from domain.common.scenario_report_cycles import (
    ReportCycleError,
    ReportCycleGuard,
    ReportNode,
)


def test_distinct_report_chain_is_allowed() -> None:
    guard = ReportCycleGuard()

    with guard.enter(1, 10):
        with guard.enter(2, 20):
            with guard.enter(3, 30):
                pass


def test_revisiting_report_node_raises_with_cycle_path() -> None:
    guard = ReportCycleGuard()

    with pytest.raises(ReportCycleError) as caught:
        with guard.enter(1, 10):
            with guard.enter(2, 20):
                with guard.enter(1, 10):
                    pass

    assert caught.value.cycle == (
        ReportNode(1, 10),
        ReportNode(2, 20),
        ReportNode(1, 10),
    )


def test_same_category_in_different_scenarios_is_not_a_cycle() -> None:
    guard = ReportCycleGuard()

    with guard.enter(1, 10):
        with guard.enter(2, 10):
            pass


def test_guard_is_reusable_after_cycle_failure() -> None:
    guard = ReportCycleGuard()

    with pytest.raises(ReportCycleError):
        with guard.enter(1, 10):
            with guard.enter(2, 20):
                with guard.enter(1, 10):
                    pass

    with guard.enter(1, 10):
        with guard.enter(2, 20):
            pass


def test_guard_state_is_isolated_between_threads() -> None:
    guard = ReportCycleGuard()
    entered = threading.Event()
    release = threading.Event()
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            with guard.enter(1, 10):
                entered.set()
                if not release.wait(2.0):
                    raise AssertionError("timeout waiting for main thread")
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=worker)
    thread.start()
    assert entered.wait(2.0)

    try:
        # Le même nœud est autorisé simultanément dans un autre thread.
        with guard.enter(1, 10):
            pass
    finally:
        release.set()
        thread.join(2.0)

    assert thread.is_alive() is False
    assert errors == []
