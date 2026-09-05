from __future__ import annotations

import os
import sys
import time
import traceback

STARTED_AT = time.perf_counter()

_phase_started = time.perf_counter()
from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import QApplication
PYSIDE_IMPORT_SECONDS = time.perf_counter() - _phase_started


def build_adapter(source: str, timings: dict[str, float]):
    phase = time.perf_counter()
    if source == "production":
        from production_read_adapter import build_production_adapter

        timings["adapter_module_import"] = time.perf_counter() - phase
        phase = time.perf_counter()
        adapter = build_production_adapter()
        timings["adapter_build"] = time.perf_counter() - phase
        return adapter

    if source != "smoke":
        raise ValueError("TEAMWORKS_QT_SOURCE doit valoir 'smoke' ou 'production'")

    from domain_read_adapter import build_domain_smoke_adapter

    timings["adapter_module_import"] = time.perf_counter() - phase
    phase = time.perf_counter()
    adapter = build_domain_smoke_adapter()
    timings["adapter_build"] = time.perf_counter() - phase
    return adapter


def _print_data_profile(prefix: str, timings: dict, *, ready_total: float | None = None, after_show: float | None = None) -> None:
    db_mode = "réseau" if bool(timings.get("people_db_is_network", False)) else "local"
    suffix = ""
    if ready_total is not None:
        suffix += f" · données prêtes {ready_total:.2f}s"
    if after_show is not None:
        suffix += f" · +{after_show:.2f}s après affichage"
    print(
        f"[Teamworks Qt POC] {prefix} · "
        f"import GestionDB {float(timings.get('people_gestiondb_import_seconds', 0.0)):.2f}s · "
        f"ouverture DB {float(timings.get('people_db_open_seconds', 0.0)):.2f}s ({db_mode}) · "
        f"SELECT/fetch {float(timings.get('people_reader_seconds', 0.0)):.2f}s · "
        f"mapping {float(timings.get('people_mapping_seconds', 0.0)):.3f}s · "
        f"{int(timings.get('people_count', 0))} personnes{suffix}"
    )


def main() -> None:
    startup_timings: dict[str, float] = {"pyside_import": PYSIDE_IMPORT_SECONDS}

    phase = time.perf_counter()
    from frugality import DIRECT_DEPENDENCIES, FrugalityProbe
    startup_timings["frugality_import"] = time.perf_counter() - phase
    probe = FrugalityProbe(started_at=STARTED_AT)

    phase = time.perf_counter()
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Teamworks Qt POC")
    qt_app.setOrganizationName("Pêle-Mêle Sports et Loisirs")
    startup_timings["qapplication"] = time.perf_counter() - phase

    phase = time.perf_counter()
    from theme_engine import ThemeEngine
    startup_timings["theme_module_import"] = time.perf_counter() - phase

    phase = time.perf_counter()
    theme_engine = ThemeEngine(qt_app)
    theme_engine.apply(dark=False)
    startup_timings["theme_apply"] = time.perf_counter() - phase

    source = os.environ.get("TEAMWORKS_QT_SOURCE", "smoke").strip().lower()
    adapter = build_adapter(source, startup_timings)
    ui_adapter = adapter

    people_loader_class = None
    activity_loader_class = None
    if source == "production":
        phase = time.perf_counter()
        from deferred_people import DeferredPeopleAdapter, ProductionPeopleLoader
        from deferred_activity import ProductionIndividualActivityLoader
        startup_timings["deferred_people_import"] = time.perf_counter() - phase
        ui_adapter = DeferredPeopleAdapter(adapter)
        people_loader_class = ProductionPeopleLoader
        activity_loader_class = ProductionIndividualActivityLoader

    phase = time.perf_counter()
    from pilot_generalities import PeopleContractsGeneralitiesPilot
    startup_timings["pilot_module_import"] = time.perf_counter() - phase

    window = None
    people_thread = None
    try:
        before_window = time.perf_counter()
        window = PeopleContractsGeneralitiesPilot(
            ui_adapter,
            activity_loader_class=activity_loader_class,
        )
        after_window = time.perf_counter()
        window.show()
        shown_at = time.perf_counter()

        data_seconds = float(getattr(window, "initial_people_load_seconds", 0.0))
        constructor_seconds = after_window - before_window
        ui_constructor_seconds = max(0.0, constructor_seconds - data_seconds)
        foundation_seconds = max(0.0, before_window - STARTED_AT)
        total_to_show_seconds = shown_at - STARTED_AT

        if people_loader_class is not None:
            window.statusBar().showMessage("Lecture seule · chargement des personnes en arrière-plan…")
            people_thread = QThread(window)
            people_worker = people_loader_class()
            people_worker.moveToThread(people_thread)
            window._people_loader_thread = people_thread
            window._people_loader_worker = people_worker

            def on_people_loaded(people, timings) -> None:
                window.people_model.replace(tuple(people))
                window.people_proxy.invalidate()
                QTimer.singleShot(0, lambda: window.people_count.setText(window._people_count_text()))
                ready_total = time.perf_counter() - STARTED_AT
                after_show = max(0.0, ready_total - total_to_show_seconds)
                _print_data_profile(
                    "profil données asynchrone",
                    dict(timings or {}),
                    ready_total=ready_total,
                    after_show=after_show,
                )
                window.statusBar().showMessage(
                    f"Lecture seule · {window.people_model.rowCount()} personnes · données prêtes en {ready_total:.2f}s"
                )
                people_thread.quit()

            def on_people_failed(details: str) -> None:
                print("[Teamworks Qt POC] Échec du chargement asynchrone des personnes :", file=sys.stderr)
                print(details, file=sys.stderr)
                window.statusBar().showMessage("Lecture seule · échec du chargement des personnes")
                people_thread.quit()

            people_worker.loaded.connect(on_people_loaded)
            people_worker.failed.connect(on_people_failed)
            people_thread.started.connect(people_worker.run)
            people_thread.start()

        def report_frugality() -> None:
            snapshot = probe.snapshot(
                direct_dependencies=len(DIRECT_DEPENDENCIES),
                startup_seconds=total_to_show_seconds,
            )
            data_label = "données bloquantes" if source == "production" else "données"
            timing = (
                f"socle {foundation_seconds:.2f}s · {data_label} {data_seconds:.2f}s · "
                f"construction UI {ui_constructor_seconds:.2f}s · premier affichage {total_to_show_seconds:.2f}s"
            )
            print(f"[Teamworks Qt POC] source={source} · {snapshot.compact()}")
            print(f"[Teamworks Qt POC] détail démarrage · {timing}")
            print(
                "[Teamworks Qt POC] profil socle · "
                f"PySide6 {startup_timings.get('pyside_import', 0.0):.2f}s · "
                f"QApplication {startup_timings.get('qapplication', 0.0):.2f}s · "
                f"import thème {startup_timings.get('theme_module_import', 0.0):.2f}s · "
                f"application thème {startup_timings.get('theme_apply', 0.0):.2f}s · "
                f"import adaptateur {startup_timings.get('adapter_module_import', 0.0):.2f}s · "
                f"construction adaptateur {startup_timings.get('adapter_build', 0.0):.2f}s · "
                f"import pilote {startup_timings.get('pilot_module_import', 0.0):.2f}s"
            )

            adapter_timings = getattr(adapter, "startup_timings", None)
            if source != "production" and isinstance(adapter_timings, dict):
                _print_data_profile("profil données", adapter_timings)

            if source != "production":
                window.statusBar().showMessage(
                    f"{snapshot.compact()} · {timing} · lecture seule · source {source}"
                )

        QTimer.singleShot(350, report_frugality)
        raise SystemExit(qt_app.exec())
    finally:
        if people_thread is not None and people_thread.isRunning():
            people_thread.quit()
            people_thread.wait(12000)
        close = getattr(adapter, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("[Teamworks Qt POC] Erreur fatale : traceback complet ci-dessous", file=sys.stderr)
        traceback.print_exc()
        raise SystemExit(1)
