"""SORTIE-003 — tests purs : payload canonique, hash, snapshots, corrections, commandes."""
from __future__ import annotations

import dataclasses
import hashlib
import json
import unicodedata
from datetime import date, datetime, timedelta, timezone

import pytest

from domain.employment.termination import (
    CheckState,
    ContractTermination,
    HrInputChecks,
    NoticeStatus,
    TerminationDomainError,
    TerminationReason,
    TerminationWorkflowStatus,
)
from domain.employment.termination_transmission import (
    PAYLOAD_SCHEMA,
    CommandType,
    CommunicatedHrItem,
    RequestCorrection,
    TerminationTransmissionSnapshot,
    TransmissionChannel,
    TransmitTermination,
    build_transmission_payload,
    canonical_json,
    canonical_transmission_payload,
    create_transmission_snapshot,
    sha256_hex,
    validate_supersession,
)

UTC = timezone.utc
T0 = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
RECORDED = datetime(2026, 11, 3, 10, 0, tzinfo=UTC)
SENT = datetime(2026, 11, 3, 9, 30, tzinfo=UTC)


def termination(**overrides) -> ContractTermination:
    values = dict(
        termination_id="term-1",
        contract_id="contract-1",
        effective_end_date=date(2026, 10, 31),
        last_worked_date=date(2026, 10, 30),
        known_at=T0,
        created_at=T0 + timedelta(hours=1),
        created_by="director-1",
        decision_date=date(2026, 9, 28),
        termination_reason=TerminationReason.END_OF_FIXED_TERM,
        notification_date=date(2026, 9, 29),
        notice_status=NoticeStatus.NONE,
        comments="note interne à ne jamais transmettre",
        hr_checks=HrInputChecks(
            hours=CheckState.NONE,
            absences=CheckState.PROVIDED,
            leave=CheckState.PROVIDED,
            variable_pay=CheckState.NONE,
            exceptional_items=CheckState.NONE,
        ),
        workflow_status=TerminationWorkflowStatus.PRET_IMPACT_EMPLOI,
    )
    values.update(overrides)
    return ContractTermination(**values)


ITEMS = (
    CommunicatedHrItem("leave", "12 jours ouvrables de congés restants"),
    CommunicatedHrItem("absences", "Arrêt maladie du 6 au 10 octobre"),
)


def assert_error(code, fn):
    with pytest.raises(TerminationDomainError) as exc:
        fn()
    assert exc.value.code == code
    return exc.value


def v1(term=None, **overrides):
    term = term or termination()
    values = dict(
        previous=None, hr_items=ITEMS, created_at=RECORDED, created_by="director-1",
        transmitted_at=SENT, transmitted_by="assistant-2", channel=TransmissionChannel.EMAIL,
        external_reference="  mail du 3/11  ", snapshot_id="snap-1",
    )
    values.update(overrides)
    return create_transmission_snapshot(term, **values)


# ------------------------------------------------------------ contrôle vs contenu

def test_payload_contains_exactly_the_communicated_fields():
    payload = build_transmission_payload(termination(), ITEMS)
    assert set(payload) == {
        "schema", "termination_id", "contract_id", "effective_end_date", "termination_reason",
        "notification_date", "last_worked_date", "notice", "hr_checks", "hr_items",
    }
    text = canonical_transmission_payload(termination(), ITEMS)
    for excluded in ("note interne", "2026-09-28", "director-1", "PRET_IMPACT_EMPLOI", "created_at", "version"):
        assert excluded not in text


def test_provided_check_is_not_content_each_provided_category_needs_a_description():
    assert_error("HR_ITEM_REQUIRED_LEAVE", lambda: build_transmission_payload(termination(), ITEMS[1:]))


def test_no_item_can_be_sent_for_a_category_declared_none():
    extra = ITEMS + (CommunicatedHrItem("hours", "10 h complémentaires"),)
    assert_error("HR_ITEM_NOT_PROVIDED_HOURS", lambda: build_transmission_payload(termination(), extra))


def test_hr_checks_and_items_are_both_present_and_distinct():
    payload = json.loads(canonical_transmission_payload(termination(), ITEMS))
    assert payload["hr_checks"] == {
        "absences": "PROVIDED", "exceptional_items": "NONE", "hours": "NONE",
        "leave": "PROVIDED", "variable_pay": "NONE",
    }
    assert payload["hr_items"] == [
        {"category": "absences", "description": "Arrêt maladie du 6 au 10 octobre"},
        {"category": "leave", "description": "12 jours ouvrables de congés restants"},
    ]


def test_unknown_data_cannot_be_transmitted():
    assert_error(
        "HR_CHECK_HOURS_UNKNOWN",
        lambda: build_transmission_payload(
            termination(workflow_status=TerminationWorkflowStatus.A_PREPARER,
                        hr_checks=HrInputChecks(absences=CheckState.NONE, leave=CheckState.NONE,
                                                variable_pay=CheckState.NONE, exceptional_items=CheckState.NONE)),
            (),
        ),
    )


@pytest.mark.parametrize("bad", [
    lambda: CommunicatedHrItem("salary", "x"),
    lambda: CommunicatedHrItem("leave", "   "),
    lambda: CommunicatedHrItem("leave", "x" * 2001),
])
def test_hr_item_validation(bad):
    with pytest.raises(TerminationDomainError):
        bad()


def test_duplicate_item_is_rejected():
    items = ITEMS + (CommunicatedHrItem("leave", "12 jours ouvrables de congés restants "),)
    assert_error("HR_ITEM_DUPLICATE", lambda: build_transmission_payload(termination(), items))


# ------------------------------------------------------------ canonicalisation

def test_canonical_format_is_exact():
    payload = canonical_transmission_payload(termination(), ITEMS)
    assert payload == (
        '{"contract_id":"contract-1","effective_end_date":"2026-10-31",'
        '"hr_checks":{"absences":"PROVIDED","exceptional_items":"NONE","hours":"NONE",'
        '"leave":"PROVIDED","variable_pay":"NONE"},'
        '"hr_items":[{"category":"absences","description":"Arrêt maladie du 6 au 10 octobre"},'
        '{"category":"leave","description":"12 jours ouvrables de congés restants"}],'
        '"last_worked_date":"2026-10-30",'
        '"notice":{"end":null,"start":null,"status":"NONE"},'
        '"notification_date":"2026-09-29",'
        '"schema":"' + PAYLOAD_SCHEMA + '",'
        '"termination_id":"term-1","termination_reason":"END_OF_FIXED_TERM"}'
    )


def test_same_information_built_differently_gives_identical_bytes():
    a = termination()
    b = termination(
        termination_reason="END_OF_FIXED_TERM",
        notice_status="NONE",
        hr_checks=HrInputChecks("NONE", "PROVIDED", "PROVIDED", "NONE", "NONE"),
        comments="autre note",
        decision_date=None,
        known_at=T0.astimezone(timezone(timedelta(hours=2))),
    )
    reversed_items = tuple(reversed(ITEMS))
    assert canonical_transmission_payload(a, ITEMS) == canonical_transmission_payload(b, reversed_items)


def test_mapping_order_does_not_change_bytes():
    first = {"b": 1, "a": {"y": date(2026, 1, 2), "x": None}, "c": [True, "é"]}
    second = {"c": [True, "é"], "a": {"x": None, "y": date(2026, 1, 2)}, "b": 1}
    assert canonical_json(first) == canonical_json(second) == '{"a":{"x":null,"y":"2026-01-02"},"b":1,"c":[true,"é"]}'


def test_unicode_is_nfc_normalized_and_stable():
    nfd = unicodedata.normalize("NFD", "Congés payés — Hélène ☃ 😀")
    nfc = unicodedata.normalize("NFC", nfd)
    assert nfd != nfc
    item_nfd = (CommunicatedHrItem("absences", "a"), CommunicatedHrItem("leave", nfd))
    item_nfc = (CommunicatedHrItem("absences", "a"), CommunicatedHrItem("leave", nfc))
    payload = canonical_transmission_payload(termination(), item_nfd)
    assert payload == canonical_transmission_payload(termination(), item_nfc)
    assert nfc in payload and "\\u" not in payload
    assert payload.encode("utf-8").decode("utf-8") == payload


def test_datetimes_are_utc_seconds_and_naive_is_rejected():
    paris = timezone(timedelta(hours=2))
    assert canonical_json({"t": datetime(2026, 1, 1, 12, 0, 0, 999, tzinfo=paris)}) == '{"t":"2026-01-01T10:00:00Z"}'
    assert_error("TIMESTAMP_TIMEZONE_REQUIRED", lambda: canonical_json({"t": datetime(2026, 1, 1)}))


@pytest.mark.parametrize(("value", "code"), [
    ({"x": 1.5}, "CANONICAL_FLOAT_FORBIDDEN"),
    ({"x": {1, 2}}, "CANONICAL_TYPE_FORBIDDEN"),
    ({1: "x"}, "CANONICAL_KEY_NOT_STRING"),
    ({"x": "\ud800"}, "CANONICAL_INVALID_UNICODE"),
    ({"é": 1, "é": 2}, "CANONICAL_DUPLICATE_KEY"),
])
def test_non_canonical_values_are_refused(value, code):
    assert_error(code, lambda: canonical_json(value))


def test_repr_is_never_used():
    class Opaque:
        def __repr__(self):
            return "opaque"

    assert_error("CANONICAL_TYPE_FORBIDDEN", lambda: canonical_json({"x": Opaque()}))


# ------------------------------------------------------------ hash

def test_hash_is_sha256_of_the_exact_utf8_bytes():
    snapshot = v1()
    assert snapshot.payload_hash == hashlib.sha256(snapshot.canonical_payload.encode("utf-8")).hexdigest()
    assert len(snapshot.payload_hash) == 64 and snapshot.payload_hash == snapshot.payload_hash.lower()


def test_identical_payload_gives_identical_hash_and_any_change_changes_it():
    base = sha256_hex(canonical_transmission_payload(termination(), ITEMS))
    assert base == sha256_hex(canonical_transmission_payload(termination(), tuple(reversed(ITEMS))))
    changed = [
        termination(effective_end_date=date(2026, 10, 30), last_worked_date=date(2026, 10, 30)),
        termination(termination_reason=TerminationReason.RESIGNATION),
        termination(notification_date=date(2026, 9, 30)),
        termination(notice_status=NoticeStatus.PROVIDED, notice_start=date(2026, 10, 1), notice_end=date(2026, 10, 31)),
    ]
    hashes = {sha256_hex(canonical_transmission_payload(term, ITEMS)) for term in changed}
    assert base not in hashes and len(hashes) == len(changed)
    other_items = (ITEMS[0], CommunicatedHrItem("absences", "Arrêt maladie du 6 au 11 octobre"))
    assert sha256_hex(canonical_transmission_payload(termination(), other_items)) != base


# ------------------------------------------------------------ snapshot et immutabilité

def test_v1_snapshot_fields():
    snapshot = v1()
    assert (snapshot.version, snapshot.supersedes_snapshot_id, snapshot.correction_reason) == (1, None, None)
    assert snapshot.created_at == RECORDED and snapshot.transmitted_at == SENT
    assert snapshot.created_by == "director-1" and snapshot.transmitted_by == "assistant-2"
    assert snapshot.channel is TransmissionChannel.EMAIL
    assert snapshot.external_reference == "mail du 3/11"
    assert v1(external_reference="   ").external_reference is None


def test_snapshot_is_immutable():
    snapshot = v1()
    for field_name, value in (("canonical_payload", "{}"), ("payload_hash", "0" * 64), ("version", 2)):
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(snapshot, field_name, value)


def test_tampered_payload_or_hash_is_rejected():
    snapshot = v1()
    data = dataclasses.asdict(snapshot)
    tampered = dict(data, canonical_payload=snapshot.canonical_payload.replace("2026-10-31", "2026-10-30"))
    assert_error("SNAPSHOT_HASH_MISMATCH", lambda: TerminationTransmissionSnapshot(**tampered))
    pretty = json.dumps(snapshot.payload, indent=2, ensure_ascii=False)
    assert_error(
        "SNAPSHOT_PAYLOAD_NOT_CANONICAL",
        lambda: TerminationTransmissionSnapshot(**dict(data, canonical_payload=pretty, payload_hash=sha256_hex(pretty))),
    )


def test_a_communication_cannot_be_recorded_before_it_happened_nor_before_known():
    assert_error("TRANSMITTED_AFTER_RECORDING", lambda: v1(transmitted_at=RECORDED + timedelta(seconds=1)))
    assert_error("TRANSMITTED_BEFORE_KNOWN", lambda: v1(transmitted_at=T0 - timedelta(days=1)))


def test_channel_is_validated():
    assert v1(channel="PORTAL").channel is TransmissionChannel.PORTAL
    assert_error("TRANSMISSION_CHANNEL_INVALID", lambda: v1(channel="API_IMPACT_EMPLOI"))


def test_expected_payload_hash_detects_changes_since_preview():
    preview = sha256_hex(canonical_transmission_payload(termination(), ITEMS))
    assert v1(expected_payload_hash=preview).payload_hash == preview
    assert_error("PAYLOAD_CHANGED_SINCE_PREVIEW", lambda: v1(expected_payload_hash="0" * 64))


# ------------------------------------------------------------ workflow V1

def test_transmission_is_the_only_way_from_ready_to_transmitted():
    term = termination()
    assert_error("TRANSMISSION_SNAPSHOT_REQUIRED",
                 lambda: term.transition_to(TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI))
    snapshot = v1(term)
    other = v1(termination(termination_id="term-2"))
    assert_error("TRANSMISSION_SNAPSHOT_MISMATCH", lambda: term.record_first_transmission(other))
    term.record_first_transmission(snapshot)
    assert term.workflow_status is TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI
    assert term.version == 0  # le domaine ne touche jamais la version persistée
    assert_error("NOT_READY_FOR_TRANSMISSION", lambda: term.record_first_transmission(snapshot))


def test_draft_termination_cannot_be_transmitted():
    term = termination(workflow_status=TerminationWorkflowStatus.A_PREPARER)
    assert_error("NOT_READY_FOR_TRANSMISSION", lambda: term.record_first_transmission(v1(term)))


# ------------------------------------------------------------ correction et supersession

def corrected(term, snapshot1, *, reason="Date de fin erronée", **overrides):
    term.request_correction(reason, requested_by="director-1", requested_at=RECORDED)
    term.update_transmittable(effective_end_date=date(2026, 10, 30), last_worked_date=date(2026, 10, 30))
    values = dict(previous=snapshot1, hr_items=ITEMS, created_at=RECORDED + timedelta(hours=2),
                  created_by="director-1", transmitted_at=RECORDED + timedelta(hours=1),
                  transmitted_by="director-1", channel=TransmissionChannel.PORTAL, snapshot_id="snap-2")
    values.update(overrides)
    return create_transmission_snapshot(term, **values)


def test_correction_creates_v2_superseding_v1_which_stays_intact():
    term = termination()
    snapshot1 = v1(term)
    term.record_first_transmission(snapshot1)
    frozen_v1 = dataclasses.asdict(snapshot1)
    snapshot2 = corrected(term, snapshot1)
    assert (snapshot2.version, snapshot2.supersedes_snapshot_id) == (2, "snap-1")
    assert snapshot2.correction_reason == "Date de fin erronée"
    assert snapshot2.payload["effective_end_date"] == "2026-10-30"
    assert snapshot2.payload_hash != snapshot1.payload_hash
    assert dataclasses.asdict(snapshot1) == frozen_v1
    assert snapshot1.payload["effective_end_date"] == "2026-10-31"
    term.record_correction_transmission(snapshot2)
    assert term.open_correction is None
    assert term.workflow_status is TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI


def test_protected_data_needs_an_open_correction():
    term = termination()
    term.record_first_transmission(v1(term))
    assert_error("CORRECTION_REQUIRED", lambda: term.update_transmittable(effective_end_date=date(2026, 10, 30)))
    term.request_correction("erreur", requested_by="d", requested_at=RECORDED)
    term.update_transmittable(effective_end_date=date(2026, 10, 30), last_worked_date=date(2026, 10, 30))
    assert_error("HR_CHECK_HOURS_UNKNOWN", lambda: term.update_transmittable(hr_checks=HrInputChecks()))


def test_correction_rules():
    term = termination()
    assert_error("CORRECTION_REQUIRES_TRANSMISSION",
                 lambda: term.request_correction("x", requested_by="d", requested_at=RECORDED))
    snapshot1 = v1(term)
    term.record_first_transmission(snapshot1)
    assert_error("CORRECTION_REASON_REQUIRED", lambda: term.request_correction(" ", requested_by="d", requested_at=RECORDED))
    term.request_correction("x", requested_by="d", requested_at=RECORDED)
    assert_error("CORRECTION_ALREADY_OPEN", lambda: term.request_correction("y", requested_by="d", requested_at=RECORDED))


def test_correction_without_any_change_is_refused():
    term = termination()
    snapshot1 = v1(term)
    term.record_first_transmission(snapshot1)
    term.request_correction("vérification", requested_by="d", requested_at=RECORDED)
    assert_error("CORRECTION_WITHOUT_CHANGE", lambda: create_transmission_snapshot(
        term, previous=snapshot1, hr_items=ITEMS, created_at=RECORDED + timedelta(hours=2), created_by="d",
        transmitted_at=RECORDED + timedelta(hours=1), transmitted_by="d", channel=TransmissionChannel.EMAIL))


def test_correction_needs_an_open_request_and_consistent_times():
    term = termination()
    snapshot1 = v1(term)
    term.record_first_transmission(snapshot1)
    term_copy = termination(workflow_status=TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI)
    assert_error("CORRECTION_NOT_OPEN", lambda: create_transmission_snapshot(
        term_copy, previous=snapshot1, hr_items=ITEMS, created_at=RECORDED, created_by="d",
        transmitted_at=RECORDED, transmitted_by="d", channel=TransmissionChannel.EMAIL))
    assert_error("CORRECTION_BEFORE_REQUEST",
                 lambda: corrected(term, snapshot1, transmitted_at=RECORDED - timedelta(minutes=1)))


def test_open_correction_blocks_closure():
    term = termination()
    term.record_first_transmission(v1(term))
    for target in (TerminationWorkflowStatus.EN_ATTENTE_RESULTATS, TerminationWorkflowStatus.RESULTATS_RECUS,
                   TerminationWorkflowStatus.DOCUMENTS_REMIS):
        term.transition_to(target)
    term.request_correction("x", requested_by="d", requested_at=RECORDED)
    assert_error("CORRECTION_OPEN", lambda: term.transition_to(TerminationWorkflowStatus.CLOTURE,
                                                              external_checklist_complete=True))


def test_supersession_rules():
    snapshot1 = v1()
    validate_supersession(None, "term-1", 1)
    assert_error("SNAPSHOT_ALREADY_TRANSMITTED", lambda: validate_supersession(snapshot1, "term-1", 1))
    assert_error("SNAPSHOT_PREDECESSOR_REQUIRED", lambda: validate_supersession(None, "term-1", 2))
    assert_error("SNAPSHOT_SUPERSESSION_FOREIGN", lambda: validate_supersession(snapshot1, "term-2", 2))
    assert_error("SNAPSHOT_VERSION_GAP", lambda: validate_supersession(snapshot1, "term-1", 3))
    data = dataclasses.asdict(snapshot1)
    assert_error("SNAPSHOT_SUPERSESSION_INVALID",
                 lambda: TerminationTransmissionSnapshot(**dict(data, supersedes_snapshot_id="x")))
    assert_error("SNAPSHOT_SUPERSESSION_CYCLE", lambda: TerminationTransmissionSnapshot(
        **dict(data, version=2, supersedes_snapshot_id="snap-1", correction_reason="r")))


# ------------------------------------------------------------ commandes idempotentes

def command(**overrides):
    values = dict(command_id="cmd-1", termination_id="term-1", expected_version=2, actor_id="director-1",
                  transmitted_at=SENT, transmitted_by="assistant-2", channel="EMAIL", hr_items=ITEMS)
    values.update(overrides)
    return TransmitTermination(**values)


def test_same_command_has_same_fingerprint_whatever_its_construction():
    a = command()
    b = command(hr_items=list(reversed(ITEMS)), channel=TransmissionChannel.EMAIL,
                transmitted_at=SENT.astimezone(timezone(timedelta(hours=1))), command_id="cmd-2")
    assert a.fingerprint(CommandType.TRANSMIT) == b.fingerprint(CommandType.TRANSMIT)


def test_fingerprint_distinguishes_operation_and_content():
    base = command().fingerprint(CommandType.TRANSMIT)
    assert command().fingerprint(CommandType.TRANSMIT_CORRECTION) != base
    for change in ({"channel": "PORTAL"}, {"expected_version": 3}, {"external_reference": "réf"},
                   {"transmitted_at": SENT - timedelta(minutes=1)}, {"hr_items": ITEMS[:1]}):
        assert command(**change).fingerprint(CommandType.TRANSMIT) != base


def test_request_correction_fingerprint():
    a = RequestCorrection("cmd-9", "term-1", 3, "erreur", "director-1")
    assert a.fingerprint() == RequestCorrection("cmd-10", "term-1", 3, "erreur", "director-1").fingerprint()
    assert a.fingerprint() != RequestCorrection("cmd-9", "term-1", 3, "autre", "director-1").fingerprint()


def test_command_validation():
    assert_error("COMMAND_ID_REQUIRED", lambda: command(command_id=" "))
    assert_error("TRANSMISSION_CHANNEL_INVALID", lambda: command(channel="FAX"))
    assert_error("TIMESTAMP_TIMEZONE_REQUIRED", lambda: command(transmitted_at=datetime(2026, 11, 3)))


def test_transmission_domain_does_not_depend_on_dpae_nor_payroll():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "domain" / "employment" / "termination_transmission.py").read_text(
        encoding="utf-8")
    code = source.split('"""', 2)[2]
    assert "dpae" not in code.lower()
    for forbidden in ("import", "neodes", "fctu", "dsn"):
        if forbidden == "import":
            continue
        assert forbidden not in code.lower()
