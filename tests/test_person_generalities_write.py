"""Pure employee-details validation and transaction contracts."""

import pytest

from application.services.person_generalities_write import (
    PersonDetails, PersonDetailsSnapshot,
    save_person_details, validate_person_details,
)


def payload(**changes):
    data = dict(last_name="DUPONT", first_name="Alice",
                address="1 rue du stade", postcode="03510", city="Bais", memo="RAS")
    data.update(changes)
    return validate_person_details(**data)


class Port:
    def __init__(self, snapshot):
        self.current = snapshot
        self.events = []
        self.affected = 1
        self.raise_on = None

    def load(self, person_id):
        self.events.append(("read", person_id))
        if self.raise_on == "read":
            raise RuntimeError("sensitive details")
        return self.current

    def update_if_unchanged(self, previous, updated):
        self.events.append(("update", previous.person_id))
        if self.raise_on == "write":
            raise RuntimeError("sensitive details")
        if self.affected == 1:
            self.current = PersonDetailsSnapshot(previous.person_id, updated)
        return self.affected

    def commit(self):
        self.events.append("commit")
        if self.raise_on == "commit":
            raise RuntimeError("sensitive details")

    def rollback(self):
        self.events.append("rollback")


def test_validation_keeps_names_and_integer_postcode():
    value = payload(last_name="  DUPONT  ", first_name=" Alice ")
    assert value.last_name == "DUPONT"
    assert value.first_name == "Alice"
    assert value.postcode == 3510


@pytest.mark.parametrize("changes", [
    {"last_name": ""}, {"first_name": " "},
    {"last_name": "X" * 101}, {"memo": "X" * 801},
    {"postcode": "35A00"}, {"postcode": "3510"},
    {"postcode": "-0010"}, {"postcode": "٣٥١٠٠"},
    {"address": "X" * 201},
    {"last_name": "A\nB"},
])
def test_invalid_details_are_rejected_before_sql(changes):
    with pytest.raises(ValueError):
        payload(**changes)


def test_optional_fields_can_be_cleared():
    p = payload(address="", postcode="", city="", memo="")
    assert (p.address, p.postcode, p.city, p.memo) == (None, None, None, None)


def test_success_commits_once_and_verifies_after_commit():
    original = PersonDetailsSnapshot(12, payload())
    port = Port(original)
    updated = payload(memo="Nouveau")
    result = save_person_details(port, original, updated)
    assert result.ok and result.committed and result.verified
    assert result.value.details == updated
    assert port.events == [("read", 12), ("update", 12), "commit", ("read", 12)]


def test_unchanged_is_never_written():
    original = PersonDetailsSnapshot(12, payload())
    port = Port(original)
    result = save_person_details(port, original, original.details)
    assert result.ok and not result.committed and result.code == "UNCHANGED"
    assert port.events == [("read", 12)]


def test_stale_snapshot_fails_before_sql():
    original = PersonDetailsSnapshot(12, payload())
    other = PersonDetailsSnapshot(12, payload(memo="Parallèle"))
    port = Port(other)
    result = save_person_details(port, original, payload(memo="Nouveau"))
    assert result.code == "CONFLICT" and not result.committed
    assert port.events == [("read", 12)]


def test_optimistic_write_conflict_rolls_back_without_commit():
    original = PersonDetailsSnapshot(12, payload())
    port = Port(original)
    port.affected = 0
    result = save_person_details(port, original, payload(memo="Nouveau"))
    assert result.code == "CONFLICT"
    assert port.events == [("read", 12), ("update", 12), "rollback"]


def test_database_write_error_rolls_back_and_redacts_driver_exception():
    original = PersonDetailsSnapshot(12, payload())
    port = Port(original)
    port.raise_on = "write"
    result = save_person_details(port, original, payload(memo="Nouveau"))
    assert result.code == "WRITE_ERROR" and not result.committed
    assert "sensitive" not in result.message
    assert port.events[-1] == "rollback"


def test_failed_read_and_disappearing_record_are_distinct():
    original = PersonDetailsSnapshot(12, payload())
    port = Port(None)
    assert save_person_details(port, original, payload(memo="Nouveau")).code == "NOT_FOUND"
    port.raise_on = "read"
    result = save_person_details(port, original, payload(memo="Nouveau"))
    assert result.code == "READ_ERROR"
    assert "sensitive" not in result.message


def test_invalid_identifier_never_accesses_database():
    previous = PersonDetailsSnapshot(True, payload())
    port = Port(previous)
    result = save_person_details(port, previous, payload(memo="Autre"))
    assert result.code == "INVALID_ID" and port.events == []


def test_postcommit_read_failure_is_not_misreported_as_rollback():
    original = PersonDetailsSnapshot(12, payload())
    port = Port(original)
    original_load = port.load
    reads = [0]
    def flaky_load(person_id):
        reads[0] += 1
        if reads[0] == 2:
            raise RuntimeError("private payload")
        return original_load(person_id)
    port.load = flaky_load
    result = save_person_details(port, original, payload(memo="Nouvelle"))
    assert not result.ok and result.committed and result.code == "READBACK_ERROR"
    assert "private" not in result.message
    assert "rollback" not in port.events
