from datetime import datetime, timezone

import pytest

from domain.hr_connections import (
    ExchangeArtifact,
    ExchangeDirection,
    ExchangeFormat,
    FileFingerprint,
)


def _format() -> ExchangeFormat:
    return ExchangeFormat.create(
        code="internal_csv_v1",
        version="1",
        media_type="text/csv",
        file_extension="csv",
    )


@pytest.mark.parametrize(
    "file_name",
    [
        "../export.csv",
        "folder/export.csv",
        r"folder\export.csv",
        ".",
        "..",
    ],
)
def test_exchange_artifact_rejects_path_like_file_names(file_name):
    with pytest.raises(ValueError):
        ExchangeArtifact.from_bytes(
            artifact_id="ART-001",
            direction=ExchangeDirection.EXPORT,
            adapter_id="internal-csv",
            exchange_format=_format(),
            file_name=file_name,
            payload=b"data",
            occurred_at=datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc),
        )


def test_exchange_artifact_rejects_boolean_byte_size():
    with pytest.raises(TypeError):
        ExchangeArtifact(
            artifact_id="ART-001",
            direction=ExchangeDirection.EXPORT,
            adapter_id="internal-csv",
            format_code="internal_csv_v1",
            file_name="export.csv",
            byte_size=True,  # type: ignore[arg-type]
            fingerprint=FileFingerprint.from_bytes(b"data"),
            occurred_at=datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc),
        )
