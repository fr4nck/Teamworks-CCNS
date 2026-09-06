from __future__ import annotations

from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sqlite3
import sys
import types

import pytest


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
GESTIONDB_PATH = TEAMWORKS / "GestionDB.py"
CONTRACT_PAGE_PATH = TEAMWORKS / "Ctrl" / "CTRL_Creation_contrat_p6.py"
CONTRACT_SCHEMA_PATH = TEAMWORKS / "Utils" / "UTILS_Contrats_schema.py"


SCHEMA_SQL = """
CREATE TABLE personnes (
    IDpersonne INTEGER PRIMARY KEY AUTOINCREMENT,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    date_naiss DATE
);

CREATE TABLE contrats (
    IDcontrat INTEGER PRIMARY KEY AUTOINCREMENT,
    IDpersonne INTEGER,
    IDclassification INTEGER,
    IDtype INTEGER,
    valeur_point INTEGER,
    date_debut DATE,
    date_fin DATE,
    date_rupture DATE,
    essai INTEGER,
    signature VARCHAR(3),
    due VARCHAR(3),
    cee_qualification VARCHAR(32),
    convention_code VARCHAR(32),
    ccns_group VARCHAR(8),
    weekly_hours REAL,
    gross_monthly_salary REAL,
    gross_annual_salary REAL,
    operation_type VARCHAR(24),
    previous_contract_id INTEGER,
    trial_period_value INTEGER,
    trial_period_unit VARCHAR(8)
);

CREATE TABLE contrats_valchamps (
    IDval_champ INTEGER PRIMARY KEY AUTOINCREMENT,
    IDchamp INTEGER,
    type VARCHAR(10),
    IDcontrat INTEGER,
    IDmodele INTEGER,
    valeur VARCHAR(800)
);
"""


class _Wizard:
    def __init__(self, contract_data, field_data):
        self.dictContrats = contract_data
        self.dictChamps = field_data


@contextmanager
def _noop_measure(*_args, **_kwargs):
    yield


def _module(name: str, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def _package(name: str, **attributes):
    module = _module(name, **attributes)
    module.__path__ = []
    return module


def _load_source_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def production_contract_modules(monkeypatch, tmp_path):
    wx_messages = []
    wx = _module(
        "wx",
        Panel=object,
        TAB_TRAVERSAL=0,
        YES_NO=1,
        NO_DEFAULT=2,
        ICON_WARNING=4,
        YES=1,
        OK=8,
        ICON_ERROR=16,
        MessageBox=lambda *args, **kwargs: wx_messages.append((args, kwargs)) or 0,
    )
    monkeypatch.setitem(sys.modules, "wx", wx)

    chemins = _module(
        "Chemins",
        GetStaticPath=lambda path="": str(tmp_path / "static" / path),
    )
    monkeypatch.setitem(sys.modules, "Chemins", chemins)

    utils = _package("Utils")
    traduction = _module("Utils.UTILS_Traduction", _=lambda value: value)
    diagnostic = _module("Utils.UTILS_Diagnostic_performance", mesurer=_noop_measure)
    fichiers = _module(
        "Utils.UTILS_Fichiers",
        GetRepUtilisateur=lambda path="": str(tmp_path / "user" / path),
        GetRepData=lambda path="": str(tmp_path / "data" / path),
    )
    mysql = _module("Utils.UTILS_MySQL", ConsommerDiagnosticConnexion=lambda _err: None)
    dates = _module(
        "Utils.UTILS_Dates",
        DateEnDateDD=lambda value: __import__("datetime").date.fromisoformat(str(value)),
    )
    cee_rates = _module("Utils.UTILS_CEE_baremes", GetApplicableRate=lambda *_args, **_kwargs: None)
    for name, module in (
        ("Utils", utils),
        ("Utils.UTILS_Traduction", traduction),
        ("Utils.UTILS_Diagnostic_performance", diagnostic),
        ("Utils.UTILS_Fichiers", fichiers),
        ("Utils.UTILS_MySQL", mysql),
        ("Utils.UTILS_Dates", dates),
        ("Utils.UTILS_CEE_baremes", cee_rates),
    ):
        monkeypatch.setitem(sys.modules, name, module)
    utils.UTILS_Traduction = traduction
    utils.UTILS_Diagnostic_performance = diagnostic
    utils.UTILS_Fichiers = fichiers
    utils.UTILS_MySQL = mysql
    utils.UTILS_Dates = dates
    utils.UTILS_CEE_baremes = cee_rates

    data_tables = _module(
        "Data.DATA_Tables",
        DB_DATA={},
        TABLES_IMPORTATION_OPTIONNELLES=(),
        TABLES_IMPORTATION_OBLIGATOIRES=(),
    )
    data = _package("Data", DATA_Tables=data_tables)
    monkeypatch.setitem(sys.modules, "Data", data)
    monkeypatch.setitem(sys.modules, "Data.DATA_Tables", data_tables)

    contract_schema = _load_source_module("Utils.UTILS_Contrats_schema", CONTRACT_SCHEMA_PATH)
    utils.UTILS_Contrats_schema = contract_schema

    gestiondb = _load_source_module("GestionDB", GESTIONDB_PATH)
    monkeypatch.setitem(sys.modules, "GestionDB", gestiondb)

    fonctions = _module(
        "FonctionsPerso",
        FrameOuverte=lambda _name: None,
        TexteHtml=object,
    )
    monkeypatch.setitem(sys.modules, "FonctionsPerso", fonctions)

    for package_name in (
        "application",
        "application.control",
        "domain",
        "domain.contracts",
        "domain.convention",
    ):
        monkeypatch.setitem(sys.modules, package_name, _package(package_name))

    monkeypatch.setitem(
        sys.modules,
        "application.control.contract_compensation_preflight",
        _module(
            "application.control.contract_compensation_preflight",
            ContractCompensationPreflight=object,
            validate_cee_daily_compensation=lambda **_kwargs: None,
            validate_ccns_annual_compensation=lambda **_kwargs: None,
            validate_ccns_monthly_compensation=lambda **_kwargs: None,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "application.control.contract_creation_rules_bridge",
        _module(
            "application.control.contract_creation_rules_bridge",
            build_ccns_creation_rules_preflight=lambda **_kwargs: None,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "application.control.contract_final_preflight",
        _module(
            "application.control.contract_final_preflight",
            ContractFinalPreflightDecision=types.SimpleNamespace(BLOCKED=object(), REVIEW=object()),
            ContractFinalPreflightService=object,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "domain.contracts.cee_compensation",
        _module("domain.contracts.cee_compensation", legal_cee_daily_minimum=lambda **_kwargs: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "domain.contracts.cee_contract_guardrails",
        _module("domain.contracts.cee_contract_guardrails", CEEContractGuardrailService=object),
    )
    monkeypatch.setitem(
        sys.modules,
        "domain.convention.seniority_timeline",
        _module(
            "domain.convention.seniority_timeline",
            CCNSContractSeniorityTimelineService=types.SimpleNamespace(
                completed_calendar_months=lambda *_args, **_kwargs: 0
            ),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "domain.convention.smic",
        _module(
            "domain.convention.smic",
            SmicTerritory=types.SimpleNamespace(METROPOLITAN_FRANCE="FR"),
            create_smic_catalog_2026=lambda: None,
        ),
    )

    page_module = _load_source_module("tw10_03_contract_page", CONTRACT_PAGE_PATH)
    return page_module, gestiondb, wx_messages


def _create_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.execute(
            "INSERT INTO personnes (IDpersonne, nom, prenom, date_naiss) VALUES (?, ?, ?, ?)",
            (1, "Salarié", "Test", "1990-02-03"),
        )


def _contract_data(*, contract_id: int = 0, end_date: str = "2027-08-31"):
    return {
        "IDcontrat": contract_id,
        "IDpersonne": 1,
        "IDclassification": None,
        "IDtype": None,
        "valeur_point": None,
        "date_debut": "2026-09-01",
        "date_fin": end_date,
        "date_rupture": None,
        "essai": 30,
    }


def _build_page(page_module, contract_data, field_data):
    wizard = _Wizard(contract_data, field_data)
    page = object.__new__(page_module.Page)
    page.GetGrandParent = lambda: wizard
    page._RunFinalPreflight = types.MethodType(lambda _self, _db, _data: True, page)
    return page


def _bind_database(page_module, db_class, path: Path):
    def factory(*_args, **_kwargs):
        return db_class(nomFichier=str(path), suffixe=None)

    page_module.GestionDB = types.SimpleNamespace(DB=factory)


def _read_rows(path: Path, query: str, parameters=()):
    with sqlite3.connect(path) as connection:
        return connection.execute(query, parameters).fetchall()


def test_contract_creation_commits_contract_and_dependent_fields_atomically(
    tmp_path, production_contract_modules
):
    page_module, gestiondb, wx_messages = production_contract_modules
    db_path = tmp_path / "teamworks_rh.dat"
    _create_database(db_path)
    _bind_database(page_module, gestiondb.DB, db_path)
    page = _build_page(page_module, _contract_data(), {12: "Valeur RH"})

    assert page_module.Page.Validation(page) is True

    contracts = _read_rows(
        db_path,
        "SELECT IDcontrat, IDpersonne, date_debut, date_fin FROM contrats",
    )
    fields = _read_rows(
        db_path,
        "SELECT IDchamp, IDcontrat, type, valeur FROM contrats_valchamps",
    )
    assert len(contracts) == 1
    assert contracts[0][1:] == (1, "2026-09-01", "2027-08-31")
    assert fields == [(12, contracts[0][0], "contrat", "Valeur RH")]
    assert _read_rows(db_path, "SELECT IDpersonne FROM personnes WHERE IDpersonne=1") == [(1,)]
    assert wx_messages == []


def test_contract_creation_rolls_back_when_dependent_field_insert_fails(
    tmp_path, production_contract_modules
):
    page_module, gestiondb, wx_messages = production_contract_modules
    db_path = tmp_path / "teamworks_rh.dat"
    _create_database(db_path)

    class FailOnContractFieldInsert(gestiondb.DB):
        def ReqInsert(self, nomTable="", listeDonnees=None, commit=True):
            if nomTable == "contrats_valchamps":
                raise RuntimeError("TW10-03 injection après insertion du contrat")
            return super().ReqInsert(
                nomTable,
                [] if listeDonnees is None else listeDonnees,
                commit=commit,
            )

    _bind_database(page_module, FailOnContractFieldInsert, db_path)
    failed_page = _build_page(page_module, _contract_data(), {12: "Valeur RH"})

    assert page_module.Page.Validation(failed_page) is False

    assert _read_rows(db_path, "SELECT IDcontrat, IDpersonne FROM contrats") == []
    assert _read_rows(db_path, "SELECT IDval_champ, IDcontrat FROM contrats_valchamps") == []
    assert _read_rows(db_path, "SELECT IDpersonne FROM personnes WHERE IDpersonne=1") == [(1,)]
    assert wx_messages and "Aucune modification n'a été validée" in wx_messages[-1][0][0]

    _bind_database(page_module, gestiondb.DB, db_path)
    success_page = _build_page(page_module, _contract_data(), {12: "Après rollback"})
    assert page_module.Page.Validation(success_page) is True

    contracts = _read_rows(db_path, "SELECT IDcontrat, IDpersonne FROM contrats")
    fields = _read_rows(db_path, "SELECT IDcontrat, valeur FROM contrats_valchamps")
    assert len(contracts) == 1
    assert contracts[0][1] == 1
    assert fields == [(contracts[0][0], "Après rollback")]


def test_contract_modification_restores_contract_and_deleted_field_when_commit_fails(
    tmp_path, production_contract_modules
):
    page_module, gestiondb, wx_messages = production_contract_modules
    db_path = tmp_path / "teamworks_rh.dat"
    _create_database(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO contrats (
                IDcontrat, IDpersonne, date_debut, date_fin, essai, signature, due
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (7, 1, "2026-09-01", "2027-08-31", 30, "oui", "oui"),
        )
        connection.execute(
            """
            INSERT INTO contrats_valchamps (
                IDval_champ, IDchamp, type, IDcontrat, IDmodele, valeur
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (9, 12, "contrat", 7, 0, "Valeur initiale"),
        )

    class FailOnFinalCommit(gestiondb.DB):
        def Commit(self):
            raise RuntimeError("TW10-03 injection avant commit final")

    _bind_database(page_module, FailOnFinalCommit, db_path)
    page = _build_page(
        page_module,
        _contract_data(contract_id=7, end_date="2028-08-31"),
        {},
    )

    assert page_module.Page.Validation(page) is False

    assert _read_rows(
        db_path,
        "SELECT IDcontrat, IDpersonne, date_fin, signature, due FROM contrats WHERE IDcontrat=7",
    ) == [(7, 1, "2027-08-31", "oui", "oui")]
    assert _read_rows(
        db_path,
        "SELECT IDval_champ, IDchamp, IDcontrat, valeur FROM contrats_valchamps WHERE IDval_champ=9",
    ) == [(9, 12, 7, "Valeur initiale")]
    assert wx_messages and "Aucune modification n'a été validée" in wx_messages[-1][0][0]
