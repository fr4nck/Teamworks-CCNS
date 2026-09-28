from datetime import date, datetime, timedelta, timezone
from threading import Barrier, Thread

import pytest

from domain.employment.termination_documents import (
    TerminationDocument, TerminationDocumentSource, TerminationDocumentType,
)
from domain.employment.termination_repository import TerminationPersistenceError
from infrastructure.persistence.mysql_termination_document_repository import MySqlTerminationDocumentRepository
from infrastructure.persistence.mysql_termination_repository import MySqlTerminationRepository
from tests.test_employee_termination_domain import ready_termination
from tests.termination_mysql_support import termination_db  # noqa: F401

NOW = datetime(2026, 10, 31, 18, 0, tzinfo=timezone.utc)


def setup_termination(connect):
    termination = ready_termination()
    MySqlTerminationRepository(connect).add(termination)
    return termination


def make_doc(termination, *, document_id="doc-1", sha="a" * 64):
    return TerminationDocument(
        document_id=document_id, termination_id=termination.termination_id,
        document_type=TerminationDocumentType.AER, source=TerminationDocumentSource.FRANCE_TRAVAIL,
        document_date=date(2026, 10, 31), received_at=NOW, received_by="director-1",
        file_reference="rh/aer.pdf", sha256=sha, external_reference="ft-123",
    )


def test_document_round_trip(termination_db):
    termination = setup_termination(termination_db)
    repo = MySqlTerminationDocumentRepository(termination_db)
    expected = make_doc(termination)
    repo.add(expected)
    actual = repo.get(expected.document_id)
    assert actual == expected
    assert repo.list_for_termination(termination.termination_id) == (expected,)


def test_same_hash_is_deduplicated_per_termination(termination_db):
    termination = setup_termination(termination_db)
    repo = MySqlTerminationDocumentRepository(termination_db)
    repo.add(make_doc(termination, document_id="doc-a"))
    with pytest.raises(TerminationPersistenceError) as exc:
        repo.add(make_doc(termination, document_id="doc-b"))
    assert exc.value.code == "DOCUMENT_DUPLICATE"
    assert len(repo.list_for_termination(termination.termination_id)) == 1


def test_archive_and_delivery_are_write_once(termination_db):
    termination = setup_termination(termination_db)
    repo = MySqlTerminationDocumentRepository(termination_db)
    document = make_doc(termination)
    repo.add(document)
    repo.mark_archived(document.document_id, at=NOW + timedelta(minutes=1), by="director-1")
    repo.mark_delivered(document.document_id, at=NOW + timedelta(minutes=2), by="director-1")
    actual = repo.get(document.document_id)
    assert actual.is_archived and actual.is_delivered
    with pytest.raises(TerminationPersistenceError) as exc:
        repo.mark_delivered(document.document_id, at=NOW + timedelta(minutes=3), by="director-2")
    assert exc.value.code == "DOCUMENT_STATE_CONFLICT"


def test_two_workers_cannot_import_same_file_twice(termination_db):
    termination = setup_termination(termination_db)
    barrier = Barrier(2)
    results = []

    def worker(document_id):
        repo = MySqlTerminationDocumentRepository(termination_db)
        barrier.wait()
        try:
            repo.add(make_doc(termination, document_id=document_id))
            results.append("ok")
        except TerminationPersistenceError as exc:
            results.append(exc.code)

    threads = [Thread(target=worker, args=("doc-a",)), Thread(target=worker, args=("doc-b",))]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=10)
    assert sorted(results) == ["DOCUMENT_DUPLICATE", "ok"]
    assert len(MySqlTerminationDocumentRepository(termination_db).list_for_termination(termination.termination_id)) == 1


def test_two_workers_cannot_deliver_same_document_twice(termination_db):
    termination = setup_termination(termination_db)
    repo = MySqlTerminationDocumentRepository(termination_db)
    document = make_doc(termination)
    repo.add(document)
    barrier = Barrier(2)
    results = []

    def worker(actor):
        local = MySqlTerminationDocumentRepository(termination_db)
        barrier.wait()
        try:
            local.mark_delivered(document.document_id, at=NOW + timedelta(minutes=2), by=actor)
            results.append("ok")
        except TerminationPersistenceError as exc:
            results.append(exc.code)

    threads = [Thread(target=worker, args=("a",)), Thread(target=worker, args=("b",))]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=10)
    assert sorted(results) == ["DOCUMENT_STATE_CONFLICT", "ok"]
