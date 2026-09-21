from __future__ import annotations

from datetime import date
from decimal import Decimal

from application.services.contract_write import (
    ContractCreateCommand,
    ContractEditCommand,
)
from infrastructure.persistence.contract_write_adapter import (
    GestionDbContractWriteAdapter,
)


MODERN_COLUMNS = (
    "IDcontrat",
    "IDpersonne",
    "IDclassification",
    "IDtype",
    "valeur_point",
    "date_debut",
    "date_fin",
    "date_rupture",
    "essai",
    "signature",
    "due",
    "convention_code",
    "ccns_group",
    "cee_qualification",
    "weekly_hours",
    "gross_monthly_salary",
    "gross_annual_salary",
    "operation_type",
    "previous_contract_id",
    "trial_period_value",
    "trial_period_unit",
)


class FakeMySqlCursor:
    def __init__(self):
        self.executed = []
        self.rowcount = 1
        self._last_query = ""

    def execute(self, query, params=None):
        self._last_query = query
        self.executed.append((query, params))
        self.rowcount = 1

    def fetchone(self):
        if "FROM personnes" in self._last_query:
            return (12,)
        if "SELECT signature" in self._last_query:
            return ("Oui",)
        if "SELECT due" in self._last_query:
            return ("",)
        if "FROM contrats c" in self._last_query:
            return (
                12,
                4,
                "CDD",
                "CDD",
                "2026-10-01",
                "2026-10-31",
                None,
                "CCNS",
                "G3",
                None,
                Decimal("35.00"),
                Decimal("3000.00"),
                None,
            )
        if "FROM contrats WHERE IDcontrat" in self._last_query:
            return (501,)
        return None

    def fetchall(self):
        if "FROM contrats_types" in self._last_query:
            return ((4, "CDD", "CDD"), (5, "CEE", "CEE"))
        return ()


class FakeMySqlDb:
    def __init__(self):
        self.isNetwork = True
        self.echec = 0
        self.cursor = FakeMySqlCursor()
        self.connexion = self
        self.req_insert_calls = []
        self.commits = 0
        self.rollbacks = 0

    def GetListeChamps2(self, table_name):
        assert table_name == "contrats"
        return tuple((name, "VARCHAR(255)") for name in MODERN_COLUMNS)

    def ReqInsert(self, table_name, data, commit=True):
        self.req_insert_calls.append((table_name, tuple(data), commit))
        return 501

    def Commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def _create_command():
    return ContractCreateCommand(
        person_id=12,
        contract_type_code="CDD",
        convention_code="CCNS",
        ccns_group="G3",
        cee_qualification=None,
        weekly_hours=Decimal("35.00"),
        gross_monthly_salary=Decimal("3000.00"),
        gross_annual_salary=None,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
        trial_period_value=0,
        trial_period_unit="DAY",
        confirm_no_trial=True,
    )


def _edit_command():
    return ContractEditCommand(
        contract_id=501,
        contract_type_code="CDD",
        convention_code="CCNS",
        ccns_group="G3",
        cee_qualification=None,
        weekly_hours=Decimal("35.00"),
        gross_monthly_salary=Decimal("3000.01"),
        gross_annual_salary=None,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 11, 1),
        break_date=None,
        modern_fields_supported=True,
    )


def test_mysql_adapter_uses_mysql_placeholders_and_never_commits_insert_itself():
    db = FakeMySqlDb()
    adapter = GestionDbContractWriteAdapter(db)

    assert adapter.person_exists(12) is True
    assert adapter.available_contract_type_codes() == ("CDD", "CEE")
    assert adapter.insert_contract(_create_command()) == 501

    assert db.req_insert_calls
    table_name, data, commit = db.req_insert_calls[0]
    assert table_name == "contrats"
    assert commit is False
    assert ("IDpersonne", 12) in data
    assert ("IDtype", 4) in data
    assert db.commits == 0

    for query, _params in db.cursor.executed:
        assert "?" not in query
        if "WHERE IDpersonne=" in query:
            assert "WHERE IDpersonne=%s" in query


def test_mysql_adapter_update_delete_and_readback_keep_mysql_parameter_style():
    db = FakeMySqlDb()
    adapter = GestionDbContractWriteAdapter(db)

    assert adapter.update_contract(_edit_command()) == 1
    snapshot = adapter.read_contract(501)
    assert snapshot is not None
    assert snapshot.contract_id == 501
    assert snapshot.contract_type_code == "CDD"

    assert adapter.update_indicator(501, "signature", "Oui") == 1
    assert adapter.read_indicator(501, "signature") == "Oui"
    assert adapter.contract_exists(501) is True
    assert adapter.delete_contract(501) == 1

    assert db.commits == 0
    assert db.rollbacks == 0
    assert db.cursor.executed

    for query, params in db.cursor.executed:
        assert "?" not in query
        if params:
            assert "%s" in query
