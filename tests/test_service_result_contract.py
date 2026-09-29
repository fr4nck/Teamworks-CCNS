# -*- coding: utf-8 -*-

from datetime import date

import pytest

from application.services.service_result import (
    BatchDisposition,
    BatchIssue,
    BatchItemRef,
    BatchReport,
    ServiceError,
    ServiceErrorCode,
    ServiceResult,
)


def test_service_result_success_ne_porte_pas_erreur():
    result = ServiceResult.success(value=123, target_id=7, committed=True)

    assert result.ok is True
    assert result.value == 123
    assert result.target_id == 7
    assert result.committed is True
    assert result.error is None
    assert result.code == "OK"


def test_service_result_failure_exige_erreur_structuree():
    error = ServiceError(
        code=ServiceErrorCode.CONCURRENT_MODIFICATION,
        message="La présence a changé.",
        target_id=12,
        expected_revision="ancienne",
        actual_revision="nouvelle",
    )
    result = ServiceResult.failure(
        error=error,
        target_id=12,
        committed=False,
    )

    assert result.ok is False
    assert result.error is error
    assert result.code == ServiceErrorCode.CONCURRENT_MODIFICATION.value
    assert result.error.expected_revision == "ancienne"
    assert result.error.actual_revision == "nouvelle"


def test_service_result_refuse_succes_avec_erreur():
    with pytest.raises(ValueError):
        ServiceResult(
            ok=True,
            error=ServiceError(
                code=ServiceErrorCode.INTERNAL_ERROR,
                message="Impossible",
            ),
        )


def test_service_result_refuse_echec_sans_erreur():
    with pytest.raises(ValueError):
        ServiceResult(ok=False)


def test_batch_report_compte_exactement_tous_les_elements():
    issue = BatchIssue(
        item=BatchItemRef(
            index=1,
            person_id=17,
            presence_date=date(2026, 9, 22),
        ),
        disposition=BatchDisposition.SKIPPED,
        error=ServiceError(
            code=ServiceErrorCode.OVERLAP_CONFLICT,
            message="Chevauchement.",
            conflicting_target_id=84,
        ),
    )

    report = BatchReport(
        requested_count=4,
        succeeded_count=3,
        skipped_count=1,
        issues=(issue,),
    )

    assert report.requested_count == 4
    assert report.succeeded_count == 3
    assert report.skipped_count == 1
    assert report.rejected_count == 0
    assert report.issues[0].error.conflicting_target_id == 84


def test_batch_report_refuse_un_bilan_incomplet():
    with pytest.raises(ValueError):
        BatchReport(
            requested_count=4,
            succeeded_count=2,
            skipped_count=1,
        )


def test_batch_report_refuse_issue_sans_compteur_associe():
    issue = BatchIssue(
        item=BatchItemRef(index=0),
        disposition=BatchDisposition.REJECTED,
        error=ServiceError(
            code=ServiceErrorCode.VALIDATION_ERROR,
            message="Entrée invalide.",
        ),
    )

    with pytest.raises(ValueError):
        BatchReport(
            requested_count=1,
            succeeded_count=1,
            issues=(issue,),
        )


def test_database_error_distingue_message_utilisateur_et_diagnostic():
    error = ServiceError(
        code=ServiceErrorCode.DATABASE_ERROR,
        message="L'enregistrement a échoué.",
        retryable=True,
        diagnostic="OperationalError: server has gone away",
    )

    assert "OperationalError" not in error.message
    assert "OperationalError" in error.diagnostic
    assert error.retryable is True


def test_readback_error_peut_signaler_commit_deja_realise():
    result = ServiceResult.failure(
        error=ServiceError(
            code=ServiceErrorCode.READBACK_ERROR,
            message="Écriture validée, relecture impossible.",
            retryable=False,
        ),
        target_id=42,
        committed=True,
    )

    assert result.ok is False
    assert result.committed is True
    assert result.error is not None
    assert result.error.retryable is False
