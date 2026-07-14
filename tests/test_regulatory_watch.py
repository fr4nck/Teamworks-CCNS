from datetime import datetime, timezone

from application.services.ccns.regulatory_watch import RegulatoryWatchService
from domain.regulatory import (
    RegulatoryChangeType,
    RegulatoryReference,
    RegulatoryReferenceKind,
    RegulatorySnapshot,
    compare_regulatory_snapshots,
)
from infrastructure.regulatory_watch import JsonRegulatorySnapshotStore


def make_reference() -> RegulatoryReference:
    return RegulatoryReference(
        code="CCNS-IDCC-2511",
        label="Convention collective nationale du sport - IDCC 2511",
        kind=RegulatoryReferenceKind.CCNS_TEXT,
        source_url="https://www.legifrance.gouv.fr/conv_coll/id/KALICONT000017577652",
        expected_scope="Texte conventionnel CCNS et avenants étendus",
    )


def make_snapshot(content: bytes, reference_code: str = "CCNS-IDCC-2511") -> RegulatorySnapshot:
    return RegulatorySnapshot.from_content(
        reference_code=reference_code,
        source_url="https://www.legifrance.gouv.fr/conv_coll/id/KALICONT000017577652",
        content=content,
        fetched_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        source_title="CCNS",
    )


def test_compare_regulatory_snapshots_detects_new_reference():
    reference = make_reference()
    current = make_snapshot(b"version initiale")

    change = compare_regulatory_snapshots(reference, None, current)

    assert change.change_type is RegulatoryChangeType.NEW_REFERENCE
    assert change.has_alert is True
    assert change.requires_human_validation is True


def test_compare_regulatory_snapshots_detects_source_change():
    reference = make_reference()
    previous = make_snapshot(b"ancienne version")
    current = make_snapshot(b"nouvelle version")

    change = compare_regulatory_snapshots(reference, previous, current)

    assert change.change_type is RegulatoryChangeType.SOURCE_CHANGED
    assert "Source modifiée" in change.summary


def test_compare_regulatory_snapshots_marks_unchanged_content():
    reference = make_reference()
    previous = make_snapshot(b"meme version")
    current = make_snapshot(b"meme version")

    change = compare_regulatory_snapshots(reference, previous, current)

    assert change.change_type is RegulatoryChangeType.UNCHANGED
    assert change.has_alert is False


def test_regulatory_watch_service_records_snapshot_without_business_update(tmp_path):
    reference = make_reference()
    store = JsonRegulatorySnapshotStore(tmp_path / "watch" / "snapshots.json")

    class StaticFetcher:
        def fetch(self, requested_reference):
            assert requested_reference == reference
            return make_snapshot(b"contenu officiel observe")

    service = RegulatoryWatchService(fetcher=StaticFetcher(), store=store)

    change = service.check_reference(reference)
    latest = store.get_latest(reference.code)

    assert change.change_type is RegulatoryChangeType.NEW_REFERENCE
    assert latest is not None
    assert latest.content_hash == make_snapshot(b"contenu officiel observe").content_hash
