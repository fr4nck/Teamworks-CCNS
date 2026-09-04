from __future__ import annotations

import time
import traceback

from PySide6.QtCore import QObject, Signal, Slot


class DeferredPeopleAdapter:
    """Décale uniquement la liste initiale des personnes.

    Les autres lectures restent déléguées à l'adaptateur réel ; les détails
    individuels utilisent en production leur worker dédié afin de ne pas bloquer l'UI.
    """

    def __init__(self, delegate):
        self._delegate = delegate

    def list_people(self):
        return ()

    def get_person_generalities(self, person_id):
        return self._delegate.get_person_generalities(person_id)

    def list_contracts(self, person_id):
        return self._delegate.list_contracts(person_id)

    def list_scenarios(self, person_id):
        return self._delegate.list_scenarios(person_id)

    def list_trips(self, person_id):
        return self._delegate.list_trips(person_id)

    def list_reimbursements(self, person_id):
        return self._delegate.list_reimbursements(person_id)

    def close(self) -> None:
        close = getattr(self._delegate, "close", None)
        if callable(close):
            close()


class ProductionPeopleLoader(QObject):
    """Charge les identités sur un worker Qt avec son propre adaptateur/reader."""

    loaded = Signal(object, object)
    failed = Signal(str)

    @Slot()
    def run(self) -> None:
        adapter = None
        started = time.perf_counter()
        try:
            phase = time.perf_counter()
            from production_read_adapter import build_production_adapter
            import_seconds = time.perf_counter() - phase

            phase = time.perf_counter()
            adapter = build_production_adapter()
            build_seconds = time.perf_counter() - phase

            people = tuple(adapter.list_people())
            timings = dict(getattr(adapter, "startup_timings", {}) or {})
            timings.update(
                {
                    "worker_import_seconds": import_seconds,
                    "worker_adapter_build_seconds": build_seconds,
                    "worker_total_seconds": time.perf_counter() - started,
                }
            )
            self.loaded.emit(people, timings)
        except Exception:
            self.failed.emit(traceback.format_exc())
        finally:
            if adapter is not None:
                try:
                    adapter.close()
                except Exception:
                    pass
