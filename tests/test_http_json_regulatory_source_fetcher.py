import json
from domain.regulatory import RegulatoryReference, RegulatoryReferenceKind
from infrastructure.regulatory_watch import HttpJsonRegulatorySourceFetcher


class FakeResponse:
    def __init__(self, content: bytes):
        self._content = content

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self._content


def test_http_json_fetcher_builds_snapshot_from_official_json_reference():
    reference = RegulatoryReference(
        code="DATAGOUV-LEGIFRANCE-API",
        label="Fiche data.gouv de l'API Légifrance",
        kind=RegulatoryReferenceKind.CCNS_GENERAL_CHANGE,
        source_url="https://www.data.gouv.fr/api/1/dataservices/legifrance/",
        expected_scope="Métadonnées officielles de l'API Légifrance",
    )
    payload = {
        "id": "legifrance",
        "title": "Légifrance",
        "last_update": "2026-07-14T00:00:00+00:00",
        "extras": {"b": 2, "a": 1},
    }

    def fake_opener(request, timeout):
        assert request.full_url == reference.source_url
        assert request.headers["Accept"] == "application/json"
        assert timeout == 3.0
        return FakeResponse(json.dumps(payload).encode("utf-8"))

    snapshot = HttpJsonRegulatorySourceFetcher(
        timeout_seconds=3.0,
        opener=fake_opener,
    ).fetch(reference)

    assert snapshot.reference_code == reference.code
    assert snapshot.source_url == reference.source_url
    assert snapshot.source_title == reference.label
    assert snapshot.effective_date.isoformat() == "2026-07-14"
    assert snapshot.metadata["format"] == "json"
    assert snapshot.metadata["source_id"] == "legifrance"
    assert snapshot.content_length == len(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
