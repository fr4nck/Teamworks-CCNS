"""Safe minimal person creation: validation, commit, rollback, readback."""

from application.services.person_generalities_create import create_person_details
from application.services.person_generalities_write import (
    PersonDetails, PersonDetailsSnapshot,
)


def details(**updates):
    base=dict(last_name="MARTIN",first_name="Élodie",
              address="Place du sport",postcode=3510,
              city="Rennes",memo="Nouvelle arrivée")
    base.update(updates)
    return PersonDetails(**base)


class FakePort:
    def __init__(self):
        self.events=[]
        self.new_id=18
        self.current=None
        self.fail=None

    def insert(self,payload):
        self.events.append(("insert",payload))
        if self.fail=="insert":
            raise RuntimeError("sensitive SQL")
        self.current=PersonDetailsSnapshot(self.new_id,payload)
        return self.new_id

    def load(self,person_id):
        self.events.append(("read",person_id))
        if self.fail=="read":
            raise RuntimeError("sensitive SQL")
        return self.current

    def commit(self):
        self.events.append("commit")
        if self.fail=="commit":
            raise RuntimeError("sensitive SQL")

    def rollback(self):
        self.events.append("rollback")


def test_creates_then_reads_back_exactly_once():
    port=FakePort()
    result=create_person_details(port,details())
    assert result.ok and result.committed and result.verified
    assert result.value.person_id==18
    assert result.value.details.postcode==3510
    assert port.events[0][0]=="insert"
    assert port.events[1:]==["commit",("read",18)]


def test_bad_data_never_calls_database():
    for bad in (details(last_name=""),details(postcode="XXXX"),
                details(memo="x"*801),details(first_name="\n"),
                details(postcode=-1),object()):
        port=FakePort()
        response=create_person_details(port,bad)
        assert not response.ok and response.code=="INVALID_FIELDS"
        assert port.events==[]


def test_insert_failure_rolls_back_and_redacts_driver_errors():
    port=FakePort()
    port.fail="insert"
    result=create_person_details(port,details())
    assert result.code=="WRITE_UNCONFIRMED"
    assert port.events[-1]=="rollback"
    assert "sensitive" not in result.message


def test_invalid_generated_id_does_not_commit():
    port=FakePort()
    port.new_id=0
    result=create_person_details(port,details())
    assert result.code=="WRITE_UNCONFIRMED"
    assert port.events[-1]=="rollback"
    assert "commit" not in port.events


def test_failed_commit_is_not_claimed_as_success():
    port=FakePort()
    port.fail="commit"
    result=create_person_details(port,details())
    assert not result.ok and not result.verified
    assert result.code=="WRITE_UNCONFIRMED"
    assert "sensitive" not in result.message


def test_after_commit_read_failure_does_not_trigger_duplicate():
    port=FakePort()
    port.fail="read"
    result=create_person_details(port,details())
    assert not result.ok and result.committed and not result.verified
    assert result.code=="READBACK_ERROR"
    assert "18" in result.message
    assert port.events==[
        ("insert",port.current.details),"commit",("read",18)
    ]
    assert "rollback" not in port.events


def test_readback_mismatch_reports_commit_without_claiming_success():
    port=FakePort()
    def different(_person_id):
        port.events.append(("read",18))
        return PersonDetailsSnapshot(18,details(memo="Autre"))
    port.load=different
    result=create_person_details(port,details())
    assert result.code=="READBACK_MISMATCH"
    assert result.committed and not result.verified
    assert result.value.person_id==18
    assert "recréez pas" in result.message
