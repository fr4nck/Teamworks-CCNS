from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class FrugalityBudget:
    startup_seconds: float = 3.0
    idle_rss_mb: float = 220.0
    direct_dependencies: int = 4


@dataclass(frozen=True)
class FrugalitySnapshot:
    startup_seconds: float
    rss_mb: float | None
    direct_dependencies: int
    budget: FrugalityBudget

    @property
    def startup_ok(self) -> bool:
        return self.startup_seconds <= self.budget.startup_seconds

    @property
    def memory_ok(self) -> bool:
        return self.rss_mb is None or self.rss_mb <= self.budget.idle_rss_mb

    @property
    def dependencies_ok(self) -> bool:
        return self.direct_dependencies <= self.budget.direct_dependencies

    @property
    def ok(self) -> bool:
        return self.startup_ok and self.memory_ok and self.dependencies_ok

    def compact(self) -> str:
        memory = "n/a" if self.rss_mb is None else f"{self.rss_mb:.0f} Mo"
        status = "OK" if self.ok else "À surveiller"
        return (
            f"Frugalité {status} · démarrage {self.startup_seconds:.2f}s · "
            f"RSS {memory} · dépendances directes {self.direct_dependencies}"
        )


class FrugalityProbe:
    """Mesures légères sans psutil ni autre dépendance supplémentaire."""

    def __init__(self, started_at: float | None = None, budget: FrugalityBudget | None = None):
        self.started_at = started_at if started_at is not None else time.perf_counter()
        self.budget = budget or FrugalityBudget()

    def snapshot(self, direct_dependencies: int) -> FrugalitySnapshot:
        return FrugalitySnapshot(
            startup_seconds=time.perf_counter() - self.started_at,
            rss_mb=_rss_mb(),
            direct_dependencies=direct_dependencies,
            budget=self.budget,
        )


def _rss_mb() -> float | None:
    if sys.platform == "win32":
        return _windows_rss_mb()
    try:
        import resource

        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return value / (1024 * 1024)
        return value / 1024
    except Exception:
        return None


def _windows_rss_mb() -> float | None:
    try:
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(counters)
        process = ctypes.windll.kernel32.GetCurrentProcess()
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(
            process, ctypes.byref(counters), counters.cb
        )
        if not ok:
            return None
        return counters.WorkingSetSize / (1024 * 1024)
    except Exception:
        return None


DIRECT_DEPENDENCIES = ("PySide6", "qt-material")
