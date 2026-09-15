from __future__ import annotations

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
