from __future__ import annotations

import time
import traceback

from PySide6.QtCore import QObject, Signal, Slot


class DeferredPeopleAdapter:
    """Décale uniquement la liste initiale des personnes.

    Les contrats restent servis par l'adaptateur réel. La fenêtre peut ainsi se
    construire et s'afficher sans attendre la connexion réseau historique.
    """

    def __init__(self, delegate):
        self._delegate = delegate

    def list_people(self):
        return ()

    def list_contracts(self, person_id):
        return self._delegate.list_contracts(person_id)

    def close(self) -> None:
        close = getattr(self._delegate, "close", None)
        if callable(close):
            close()


class ProductionPeopleLoader(QObject):
    """Charge les identités sur un worker Qt avec son propre adaptateur/reader.

    Le worker possède donc sa propre connexion de lecture et la ferme dans son
    thread avant de notifier l'UI. Aucun widget n'est manipulé hors du thread Qt
    principal.
    """

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
                    # Le chargement a déjà produit son résultat/erreur ; la fermeture
                    # reste best-effort et ne doit pas masquer le diagnostic principal.
                    pass
