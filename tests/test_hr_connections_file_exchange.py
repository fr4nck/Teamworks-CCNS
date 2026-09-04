import hashlib
from datetime import datetime, timezone

import pytest

from domain.hr_connections import (
    ExchangeArtifact,
    ExchangeDirection,
    ExchangeFormat,
    ExchangeValidationIssue,
    ExchangeValidationResult,
    FileExchangeDescriptor,
    FileFingerprint,
    ValidationSeverity,
)


def _format() -> ExchangeFormat:
    return ExchangeFormat.create(
        code="internal_csv_v1",
        version="1",
        media_type="text/csv",
        file_extension=".CSV",
    )


def test_exchange_format_normalizes_extension_and_media_type():
    exchange_format = _format()

    assert exchange_format.code == "internal_csv_v1"
    assert exchange_format.version == "1"
    assert exchange_format.media_type == "text/csv"
    assert exchange_format.file_extension == "csv"


def test_exchange_format_rejects_invalid_mime_and_extension():
    with pytest.raises(ValueError):
        ExchangeFormat.create(
            code="csv",
            version="1",
            media_type="text-csv",
            file_extension="csv",
        )
    with pytest.raises(ValueError):
        ExchangeFormat.create(
            code="csv",
            version="1",
            media_type="text/csv",
            file_extension="../csv",
        )


def test_file_fingerprint_is_sha256_and_rejects_invalid_values():
    payload = b"employee_id;status\n42;prepared\n"
    fingerprint = FileFingerprint.from_bytes(payload)

    assert fingerprint.algorithm == "sha256"
    assert fingerprint.digest == hashlib.sha256(payload).hexdigest()

    with pytest.raises(TypeError):
        FileFingerprint.from_bytes("payload")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        FileFingerprint(algorithm="md5", digest="0" * 32)
    with pytest.raises(ValueError):
        FileFingerprint(algorithm="sha256", digest="not-hex".ljust(64, "x"))


def test_exchange_artifact_keeps_only_metadata_and_fingerprint():
    payload = b"employee_id;status\n42;prepared\n"
    artifact = ExchangeArtifact.from_bytes(
        artifact_id=" ART-001 ",
        direction=ExchangeDirection.EXPORT,
        adapter_id=" internal-csv ",
        exchange_format=_format(),
        file_name=" export-rh.csv ",
        payload=payload,
        occurred_at=datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc),
    )

    assert artifact.artifact_id == "ART-001"
    assert artifact.adapter_id == "internal-csv"
    assert artifact.format_code == "internal_csv_v1"
    assert artifact.file_name == "export-rh.csv"
    assert artifact.byte_size == len(payload)
    assert artifact.fingerprint.digest == hashlib.sha256(payload).hexdigest()
    assert not hasattr(artifact, "payload")
    assert not hasattr(artifact, "content")


def test_exchange_artifact_rejects_paths_and_naive_timestamps():
    payload = b"data"

    with pytest.raises(ValueError):
        ExchangeArtifact.from_bytes(
            artifact_id="ART",
            direction=ExchangeDirection.IMPORT,
            adapter_id="adapter",
            exchange_format=_format(),
            file_name="../secret.csv",
            payload=payload,
            occurred_at=datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc),
        )
    with pytest.raises(ValueError):
        ExchangeArtifact.from_bytes(
            artifact_id="ART",
            direction=ExchangeDirection.IMPORT,
            adapter_id="adapter",
            exchange_format=_format(),
            file_name="file.csv",
            payload=payload,
            occurred_at=datetime(2026, 9, 1, 9, 0),
        )


def test_validation_result_warnings_do_not_invalidate_file():
    warning = ExchangeValidationIssue.create(
        code="optional_column_missing",
        message="Une colonne facultative est absente.",
        severity=ValidationSeverity.WARNING,
        location="header",
    )
    result = ExchangeValidationResult.from_issues([warning])

    assert result.is_valid
    assert result.errors == ()
    assert result.warnings == (warning,)


def test_validation_result_errors_invalidate_file():
    error = ExchangeValidationIssue.create(
        code="missing_employee_id",
        message="La colonne employee_id est obligatoire.",
        severity=ValidationSeverity.ERROR,
        location="header",
    )
    warning = ExchangeValidationIssue.create(
        code="unknown_optional_column",
        message="Une colonne facultative est inconnue.",
        severity=ValidationSeverity.WARNING,
    )
    result = ExchangeValidationResult.from_issues([warning, error])

    assert not result.is_valid
    assert result.errors == (error,)
    assert result.warnings == (warning,)


def test_file_exchange_descriptor_declares_supported_directions():
    descriptor = FileExchangeDescriptor.create(
        adapter_id="internal-csv",
        exchange_format=_format(),
        directions=[ExchangeDirection.IMPORT, ExchangeDirection.EXPORT],
    )

    assert descriptor.supports(ExchangeDirection.IMPORT)
    assert descriptor.supports(ExchangeDirection.EXPORT)

    with pytest.raises(ValueError):
        FileExchangeDescriptor.create(
            adapter_id="internal-csv",
            exchange_format=_format(),
            directions=[],
        )


def test_fake_adapter_validates_bytes_without_file_or_network_io():
    class FakeCsvAdapter:
        descriptor = FileExchangeDescriptor.create(
            adapter_id="fake-csv",
            exchange_format=_format(),
            directions=[ExchangeDirection.IMPORT],
        )

        def validate(self, *, direction, file_name, payload):
            if not self.descriptor.supports(direction):
                return ExchangeValidationResult.from_issues(
                    [
                        ExchangeValidationIssue.create(
                            code="unsupported_direction",
                            message="Sens d'échange non pris en charge.",
                            severity=ValidationSeverity.ERROR,
                        )
                    ]
                )
            if not isinstance(payload, bytes):
                raise TypeError("payload")
            if not file_name.endswith(".csv"):
                return ExchangeValidationResult.from_issues(
                    [
                        ExchangeValidationIssue.create(
                            code="invalid_extension",
                            message="Extension invalide.",
                            severity=ValidationSeverity.ERROR,
                        )
                    ]
                )
            if not payload.startswith(b"employee_id;"):
                return ExchangeValidationResult.from_issues(
                    [
                        ExchangeValidationIssue.create(
                            code="invalid_header",
                            message="En-tête invalide.",
                            severity=ValidationSeverity.ERROR,
                        )
                    ]
                )
            return ExchangeValidationResult.ok()

    adapter = FakeCsvAdapter()

    assert adapter.validate(
        direction=ExchangeDirection.IMPORT,
        file_name="input.csv",
        payload=b"employee_id;status\n42;prepared\n",
    ).is_valid
    assert not adapter.validate(
        direction=ExchangeDirection.EXPORT,
        file_name="output.csv",
        payload=b"employee_id;status\n42;prepared\n",
    ).is_valid
    assert not adapter.validate(
        direction=ExchangeDirection.IMPORT,
        file_name="input.txt",
        payload=b"employee_id;status\n42;prepared\n",
    ).is_valid
