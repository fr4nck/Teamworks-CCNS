from application.services.person_delete import (
    BLOCK_CONTRACTS,
    BLOCK_PRESENCES,
    BLOCK_REIMBURSEMENTS,
    BLOCK_TRAVEL,
    check_person_deletion,
    delete_person,
)


class FakeRepository:
    def __init__(self, blocked=None):
        self.blocked = blocked
        self.deleted = []

    def has_contracts(self, person_id):
        return self.blocked == BLOCK_CONTRACTS

    def has_presences(self, person_id):
        return self.blocked == BLOCK_PRESENCES

    def has_travel(self, person_id):
        return self.blocked == BLOCK_TRAVEL

    def has_reimbursements(self, person_id):
        return self.blocked == BLOCK_REIMBURSEMENTS

    def delete_person_with_dependents(self, person_id):
        self.deleted.append(person_id)


def test_delete_check_allows_unreferenced_person():
    result = check_person_deletion(42, FakeRepository())
    assert result.allowed is True
    assert result.blocking_reason is None


def test_delete_check_preserves_legacy_blocking_priority():
    for reason in (BLOCK_CONTRACTS, BLOCK_PRESENCES, BLOCK_TRAVEL, BLOCK_REIMBURSEMENTS):
        result = check_person_deletion(42, FakeRepository(blocked=reason))
        assert result.allowed is False
        assert result.blocking_reason == reason


def test_delete_does_not_touch_repository_when_blocked():
    repository = FakeRepository(blocked=BLOCK_CONTRACTS)
    result = delete_person(42, repository)
    assert result.allowed is False
    assert repository.deleted == []


def test_delete_calls_repository_once_when_allowed():
    repository = FakeRepository()
    result = delete_person(42, repository)
    assert result.allowed is True
    assert repository.deleted == [42]
