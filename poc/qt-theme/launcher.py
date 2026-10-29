from __future__ import annotations

import os
import sys
import time
import traceback

STARTED_AT = time.perf_counter()

_phase_started = time.perf_counter()
from PySide6.QtCore import QObject, QThread, QTimer, Slot
from PySide6.QtWidgets import QApplication, QLabel
PYSIDE_IMPORT_SECONDS = time.perf_counter() - _phase_started


class _GuiThreadReceiver(QObject):
    """Receives worker signals in the GUI thread.

    A plain Python callable connected to a worker signal runs in the worker
    thread; the people model must only be touched from the GUI thread.
    """

    def __init__(self, parent, on_loaded, on_failed):
        super().__init__(parent)
        self._on_loaded = on_loaded
        self._on_failed = on_failed

    @Slot(object, object)
    def loaded(self, people, timings) -> None:
        self._on_loaded(people, timings)

    @Slot(str)
    def failed(self, details: str) -> None:
        self._on_failed(details)


def install_french_qt_translation(qt_app) -> bool:
    """Translate Qt standard buttons and dialogs (Enregistrer, Annuler, Oui…)."""
    from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator

    translator = QTranslator(qt_app)
    directory = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if not translator.load(QLocale(QLocale.Language.French), "qtbase", "_", directory):
        print("[Teamworks Qt POC] Traduction Qt française introuvable : " + directory, file=sys.stderr)
        return False
    qt_app.installTranslator(translator)
    QLocale.setDefault(QLocale(QLocale.Language.French, QLocale.Country.France))
    return True


def frozen_paths_added_by_chemins(before, after, runtime_dir):
    """Sous-dossiers du runtime figé ajoutés à sys.path par ``import Chemins``.

    En exécutable PyInstaller, Chemins insère chaque sous-dossier du répertoire
    de l'exe (charset_normalizer, numpy…) : un ``import models`` y résoudrait
    alors ``charset_normalizer.models``. Seules ces entrées nouvelles sont visées.
    """
    base = os.path.normcase(os.path.abspath(runtime_dir))
    existing = set(before)
    added = []
    for entry in after:
        if not entry or entry in existing:
            continue
        normalized = os.path.normcase(os.path.abspath(entry))
        if normalized != base and os.path.dirname(normalized) == base:
            added.append(entry)
    return added


def import_chemins_safely() -> None:
    before = list(sys.path)
    import Chemins  # noqa: F401  (résolution des chemins Teamworks)

    if getattr(sys, "frozen", False):
        for entry in frozen_paths_added_by_chemins(before, list(sys.path), os.path.dirname(sys.executable)):
            while entry in sys.path:
                sys.path.remove(entry)


ACTIVE_DATABASE_LABEL = ""


def describe_active_database(db) -> str:
    """Libellé de la base réellement ouverte, sans mot de passe."""
    name = str(getattr(db, "nomFichier", "") or "")
    if getattr(db, "isNetwork", False):
        from infrastructure.persistence.legacy_network_target import parse_legacy_network_target

        try:
            target = parse_legacy_network_target(name)
        except ValueError:
            return "Base réseau MySQL (référence illisible)"
        return f"Base réseau MySQL « {target.database} » sur {target.host}:{target.port} · utilisateur {target.user}"
    return f"Base locale SQLite {name}"


def precheck_production_database():
    """Lecture seule : la base configurée est-elle exploitable par Qt ?

    Renvoie ``(rapport, message_bloquant)``. Aucune écriture, aucune migration.
    """
    global ACTIVE_DATABASE_LABEL
    import_chemins_safely()
    import GestionDB
    from Utils import UTILS_Fichiers
    from infrastructure.persistence.current_database_config import read_current_database_name
    from infrastructure.persistence.qt_schema_compatibility import check_schema

    config_path = UTILS_Fichiers.GetRepUtilisateur("Config.json")
    if not read_current_database_name(config_path):
        return None, (
            "Aucune base Teamworks n'est sélectionnée dans la configuration "
            f"({config_path}).\n\n"
            "Ouvrez ou créez d'abord le fichier voulu dans Teamworks, "
            "puis relancez Teamworks Qt. Aucune base n'a été ouverte."
        )

    db = GestionDB.DB()
    ACTIVE_DATABASE_LABEL = describe_active_database(db)
    print("[Teamworks Qt] " + ACTIVE_DATABASE_LABEL)
    try:
        if getattr(db, "echec", 1) != 0:
            detail = getattr(db, "erreur", "") or "fichier introuvable ou illisible"
            return None, (
                "Impossible d'ouvrir la base de données configurée "
                f"({ACTIVE_DATABASE_LABEL}).\n\n"
                f"Détail : {detail}"
            )
        report = check_schema(db)
    finally:
        try:
            db.Close()
        except Exception:
            pass
    if not report.compatible:
        return report, "Cette base n'est pas compatible avec Teamworks Qt :\n\n" + report.blocking_text()
    return report, ""


DIAGNOSTIC_ARGUMENT = "--diagnostic-mysql"


def _write_diagnostic_report(directory: str, text: str, now) -> str:
    """Écrit le rapport dans un fichier neuf, sans jamais en écraser un autre."""
    stem = os.path.join(directory, "diagnostic-mysql-" + now.strftime("%Y%m%d-%H%M%S"))
    for index in range(1, 1000):
        path = stem + ("" if index == 1 else f"-{index}") + ".txt"
        try:
            with open(path, "x", encoding="utf-8") as stream:
                stream.write(text)
            return path
        except FileExistsError:
            continue
    raise FileExistsError(stem)


def run_mysql_diagnostic_command(qt_app) -> int:
    """``--diagnostic-mysql`` : cinq étapes en lecture seule, rapport sans secret.

    Code 0 si toutes les étapes passent, 6 sinon. Aucune base n'est modifiée.
    """
    from datetime import datetime

    import_chemins_safely()
    import GestionDB
    from Utils import UTILS_Fichiers
    from infrastructure.persistence.current_database_config import read_current_database_name
    from infrastructure.persistence.mysql_connection_diagnostic import run_mysql_diagnostic
    from infrastructure.persistence.qt_schema_compatibility import check_schema

    now = datetime.now()
    config_path = UTILS_Fichiers.GetRepUtilisateur("Config.json")
    reference = read_current_database_name(config_path)
    if "[RESEAU]" not in reference:
        text = (
            "Diagnostic MySQL Teamworks Qt — lecture seule\n"
            f"Configuration lue : {config_path}\n"
            + ("Aucune base n'est sélectionnée." if not reference else "La base sélectionnée est une base locale SQLite.")
            + "\nRésultat : NON CONFORME — aucune base réseau MySQL à diagnostiquer\n"
        )
        ok = False
    else:
        def schema_report():
            db = GestionDB.DB()
            try:
                if getattr(db, "echec", 1) != 0:
                    raise RuntimeError(str(getattr(db, "erreur", "") or "ouverture impossible"))
                return check_schema(db)
            finally:
                try:
                    db.Close()
                except Exception:
                    pass

        connector = GestionDB.mysql.connector if GestionDB.IMPORT_MYSQLCONNECTOR_OK else None
        report = run_mysql_diagnostic(
            reference,
            connector=connector,
            open_connection=GestionDB.GetConnexionReseau,
            check_schema=schema_report,
            decode_password=GestionDB.DecodeMdpReseau,
            tls_label=(
                "TLS avec les certificats configurés" if GestionDB.CERTIFICATS_SSL.get("ca")
                else "désactivé, aucun certificat configuré (comportement de Teamworks wx)"
            ),
            now=now,
        )
        text = report.text().replace("Cible :", f"Configuration lue : {config_path}\nCible :", 1)
        ok = report.ok
    directory = os.environ.get("TEAMWORKS_QT_DIAGNOSTIC_DIR") or os.path.dirname(config_path)
    path = _write_diagnostic_report(directory, text, now)
    print(text)
    if not os.environ.get("TEAMWORKS_QT_AUTOCLOSE_MS"):
        from PySide6.QtWidgets import QMessageBox

        show = QMessageBox.information if ok else QMessageBox.warning
        show(None, "Teamworks Qt — diagnostic MySQL", text + "\nRapport enregistré : " + path)
    return 0 if ok else 6


def refuse_database(qt_app, message: str) -> int:
    print("[Teamworks Qt] Base refusée : " + message.replace("\n", " "), file=sys.stderr)
    if not os.environ.get("TEAMWORKS_QT_AUTOCLOSE_MS"):
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(None, "Teamworks Qt — base de données", message)
    return 3


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


def start_people_loader(window, people_loader_class, total_to_show_seconds: float):
    """Start and register the initial production people loader.

    The window owns the QThread for its complete lifetime. Late results are ignored
    once shutdown starts, while thread/worker references are cleared on finished.
    """
    thread = QThread(window)
    worker = people_loader_class()
    worker.moveToThread(thread)
    window.attach_people_loader(thread, worker)

    def on_people_loaded(people, timings) -> None:
        if window.is_closing_requested():
            thread.quit()
            return
        window.people_model.replace(tuple(people))
        window.people_proxy.invalidate()
        window.people_count.setText(window._people_count_text())
        ready_total = time.perf_counter() - STARTED_AT
        after_show = max(0.0, ready_total - total_to_show_seconds)
        _print_data_profile(
            "profil données asynchrone",
            dict(timings or {}),
            ready_total=ready_total,
            after_show=after_show,
        )
        notice = getattr(window, "schema_notice", "")
        window.statusBar().showMessage(
            f"{window.people_model.rowCount()} personnes · données prêtes en {ready_total:.2f}s"
            + (f" · {notice}" if notice else "")
        )
        thread.quit()

    def on_people_failed(details: str) -> None:
        if not window.is_closing_requested():
            print("[Teamworks Qt POC] Échec du chargement asynchrone des personnes :", file=sys.stderr)
            print(details, file=sys.stderr)
            window.statusBar().showMessage("Échec du chargement des personnes")
        thread.quit()

    receiver = _GuiThreadReceiver(window, on_people_loaded, on_people_failed)
    worker.loaded.connect(receiver.loaded)
    worker.failed.connect(receiver.failed)
    thread.started.connect(worker.run)
    thread.start()
    return thread


def main() -> None:
    startup_timings: dict[str, float] = {"pyside_import": PYSIDE_IMPORT_SECONDS}

    phase = time.perf_counter()
    from frugality import DIRECT_DEPENDENCIES, FrugalityProbe
    startup_timings["frugality_import"] = time.perf_counter() - phase
    probe = FrugalityProbe(started_at=STARTED_AT)

    phase = time.perf_counter()
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName(
        os.environ.get("TEAMWORKS_QT_APP_NAME", "Teamworks Qt POC")
    )
    qt_app.setOrganizationName("Pêle-Mêle Sports et Loisirs")
    install_french_qt_translation(qt_app)
    startup_timings["qapplication"] = time.perf_counter() - phase
    if DIAGNOSTIC_ARGUMENT in sys.argv[1:]:
        raise SystemExit(run_mysql_diagnostic_command(qt_app))

    phase = time.perf_counter()
    from theme_engine import ThemeEngine
    startup_timings["theme_module_import"] = time.perf_counter() - phase

    phase = time.perf_counter()
    theme_engine = ThemeEngine(qt_app)
    theme_engine.apply(dark=False)
    startup_timings["theme_apply"] = time.perf_counter() - phase

    source = os.environ.get("TEAMWORKS_QT_SOURCE", "smoke").strip().lower()
    schema_report = None
    if source == "production":
        phase = time.perf_counter()
        schema_report, refusal = precheck_production_database()
        startup_timings["schema_precheck"] = time.perf_counter() - phase
        if refusal:
            raise SystemExit(refuse_database(qt_app, refusal))
    adapter = build_adapter(source, startup_timings)
    ui_adapter = adapter

    people_loader_class = None
    activity_loader_class = None
    contract_write_port_factory = None
    reimbursement_write_port_factory = None
    trip_write_port_factory = None
    contract_document_workspace_factory = None
    presence_write_port_factory = None
    person_details_write_port_factory = None
    contract_schema_port = None
    if source == "production":
        phase = time.perf_counter()
        from deferred_people import DeferredPeopleAdapter, ProductionPeopleLoader
        from deferred_activity import ProductionIndividualActivityLoader
        startup_timings["deferred_people_import"] = time.perf_counter() - phase
        ui_adapter = DeferredPeopleAdapter(adapter)
        people_loader_class = ProductionPeopleLoader
        activity_loader_class = ProductionIndividualActivityLoader
        contract_write_port_factory = adapter.build_contract_write_port
        reimbursement_write_port_factory = adapter.build_reimbursement_write_port
        trip_write_port_factory = adapter.build_trip_write_port
        contract_document_workspace_factory = adapter.prepare_contract_document_workspace
        presence_write_port_factory = adapter.build_presence_write_port
        person_details_write_port_factory = adapter.build_person_details_write_port
        contract_schema_port = adapter

    phase = time.perf_counter()
    from pilot_generalities import PeopleContractsGeneralitiesPilot
    startup_timings["pilot_module_import"] = time.perf_counter() - phase

    window = None
    try:
        before_window = time.perf_counter()
        window = PeopleContractsGeneralitiesPilot(
            ui_adapter,
            activity_loader_class=activity_loader_class,
            contract_write_port_factory=contract_write_port_factory,
            reimbursement_write_port_factory=reimbursement_write_port_factory,
            trip_write_port_factory=trip_write_port_factory,
            contract_document_workspace_factory=contract_document_workspace_factory,
            presence_write_port_factory=presence_write_port_factory,
            person_details_write_port_factory=person_details_write_port_factory,
            contract_schema_port=contract_schema_port,
        )
        after_window = time.perf_counter()
        if ACTIVE_DATABASE_LABEL:
            active_label = QLabel(ACTIVE_DATABASE_LABEL)
            active_label.setObjectName("activeDatabaseLabel")
            active_label.setAccessibleName(ACTIVE_DATABASE_LABEL)
            active_label.setAccessibleDescription("Base active")
            active_label.setToolTip(ACTIVE_DATABASE_LABEL)
            window.statusBar().addPermanentWidget(active_label)
            window.setWindowTitle(f"{window.windowTitle()} — {ACTIVE_DATABASE_LABEL}")
        if schema_report is not None and schema_report.missing_contract_columns:
            window.schema_notice = schema_report.summary()
            print("[Teamworks Qt] " + schema_report.summary())
        window.show()
        shown_at = time.perf_counter()

        try:
            auto_close_ms = int(os.environ.get("TEAMWORKS_QT_AUTOCLOSE_MS", "0") or "0")
        except ValueError:
            auto_close_ms = 0
        if auto_close_ms > 0:
            QTimer.singleShot(auto_close_ms, qt_app.quit)

        data_seconds = float(getattr(window, "initial_people_load_seconds", 0.0))
        constructor_seconds = after_window - before_window
        ui_constructor_seconds = max(0.0, constructor_seconds - data_seconds)
        foundation_seconds = max(0.0, before_window - STARTED_AT)
        total_to_show_seconds = shown_at - STARTED_AT

        if people_loader_class is not None:
            window.statusBar().showMessage("Chargement des personnes en arrière-plan…")
            start_people_loader(window, people_loader_class, total_to_show_seconds)

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
        if window is not None:
            stopped = window.stop_background_threads(wait_timeout_ms=100)
            if not stopped:
                print(
                    "[Teamworks Qt POC] Fermeture : lecture synchrone encore active après le délai court ; "
                    "attente jusqu'au retour du worker afin de ne pas détruire un QThread actif.",
                    file=sys.stderr,
                )
                window.stop_background_threads(wait_timeout_ms=None)
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
