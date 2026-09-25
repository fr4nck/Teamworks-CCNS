import datetime

from application.services.person_summary import (
    PersonSummaryContract,
    select_contract_summary,
)


def contract(start, end=None, rupture="", indefinite="non", classification="Animateur"):
    return PersonSummaryContract(classification, start, end, rupture, indefinite)


TODAY = datetime.date(2026, 9, 25)


def test_no_contract():
    result = select_contract_summary([], TODAY)
    assert result.kind == "none"
    assert result.contract is None
    assert result.active is False


def test_current_fixed_contract():
    result = select_contract_summary([contract("2026-09-01", "2026-10-01")], TODAY)
    assert result.kind == "current_fixed"
    assert result.active is True


def test_last_fixed_contract():
    result = select_contract_summary([contract("2026-01-01", "2026-06-30")], TODAY)
    assert result.kind == "last_fixed"
    assert result.active is False


def test_next_fixed_contract():
    result = select_contract_summary([contract("2026-10-01", "2026-12-31")], TODAY)
    assert result.kind == "next_fixed"


def test_current_indefinite_contract():
    result = select_contract_summary(
        [contract("2026-01-01", None, "", "oui")], TODAY
    )
    assert result.kind == "current_indefinite"
    assert result.active is True


def test_indefinite_contract_with_past_rupture_is_last():
    result = select_contract_summary(
        [contract("2026-01-01", None, "2026-08-31", "oui")], TODAY
    )
    assert result.kind == "last_ended"
    assert result.active is False


def test_historical_ordering_keeps_last_candidate_until_active_found():
    result = select_contract_summary(
        [
            contract("2025-01-01", "2025-12-31", classification="Ancien"),
            contract("2026-10-01", "2026-12-31", classification="Futur"),
        ],
        TODAY,
    )
    assert result.kind == "next_fixed"
    assert result.contract.classification == "Futur"
