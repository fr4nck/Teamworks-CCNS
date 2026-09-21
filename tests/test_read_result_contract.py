# -*- coding: utf-8 -*-

from dataclasses import dataclass

import pytest

from application.services.read_result import (
    ReadCompleteness,
    ReadIssue,
    ReadIssueCode,
    ReadResult,
    ReadRetryPolicy,
    ReadSourceRequirement,
    optional_source_unavailable,
    required_source_unavailable,
)


@dataclass(frozen=True)
class DummySnapshot:
    label: str


def test_complete_exige_une_valeur_et_aucun_incident():
    result = ReadResult.complete(DummySnapshot("ok"))

    assert result.completeness is ReadCompleteness.COMPLETE
    assert result.ok is True
    assert result.partial is False
    assert result.primary_issue is None
    assert result.user_retry_allowed is False

    with pytest.raises(ValueError):
        ReadResult(
            completeness=ReadCompleteness.COMPLETE,
            value=None,
        )


def test_partial_autorise_uniquement_des_incidents_non_bloquants():
    issue = optional_source_unavailable(
        source="vacations",
        message="Vacances indisponibles.",
    )
    result = ReadResult.partial_result(
        value=DummySnapshot("dégradé"),
        issues=(issue,),
    )

    assert result.ok is True
    assert result.partial is True
    assert result.primary_issue is issue
    assert result.automatic_retry_allowed is True
    assert result.user_retry_allowed is True

    with pytest.raises(ValueError):
        ReadResult.partial_result(
            value=DummySnapshot("invalide"),
            issues=(
                required_source_unavailable(
                    source="presences",
                    message="Présences indisponibles.",
                ),
            ),
        )


def test_failed_exige_un_incident_bloquant_et_aucune_valeur():
    issue = required_source_unavailable(
        source="presences",
        message="Présences indisponibles.",
    )
    result = ReadResult.failed(issues=(issue,))

    assert result.ok is False
    assert result.completeness is ReadCompleteness.FAILED
    assert result.value is None
    assert result.primary_issue is issue

    with pytest.raises(ValueError):
        ReadResult.failed(
            issues=(
                optional_source_unavailable(
                    source="vacations",
                    message="Vacances indisponibles.",
                ),
            ),
        )


def test_retry_automatique_est_limite_a_une_seule_nouvelle_tentative():
    result = ReadResult.failed(
        issues=(
            required_source_unavailable(
                source="presences",
                message="Présences indisponibles.",
                retry_policy=ReadRetryPolicy.AUTOMATIC_ONCE,
            ),
        ),
    )

    assert result.should_retry_automatically(0) is True
    assert result.should_retry_automatically(1) is False
    assert result.should_retry_automatically(2) is False

    with pytest.raises(ValueError):
        result.should_retry_automatically(-1)


def test_user_action_autorise_refresh_manuel_sans_retry_automatique():
    result = ReadResult.failed(
        issues=(
            required_source_unavailable(
                source="presences",
                message="Présences indisponibles.",
                retry_policy=ReadRetryPolicy.USER_ACTION,
            ),
        ),
    )

    assert result.automatic_retry_allowed is False
    assert result.should_retry_automatically(0) is False
    assert result.user_retry_allowed is True


def test_never_interdit_toute_nouvelle_tentative_conseillee():
    issue = ReadIssue(
        code=ReadIssueCode.SOURCE_DATA_INVALID,
        message="Données invalides.",
        source="presences",
        requirement=ReadSourceRequirement.REQUIRED,
        retry_policy=ReadRetryPolicy.NEVER,
    )
    result = ReadResult.failed(issues=(issue,))

    assert result.should_retry_automatically(0) is False
    assert result.user_retry_allowed is False


def test_priorite_bloquante_devance_source_optionnelle():
    optional_issue = optional_source_unavailable(
        source="vacations",
        message="Vacances indisponibles.",
        retry_policy=ReadRetryPolicy.USER_ACTION,
    )
    required_issue = required_source_unavailable(
        source="presences",
        message="Présences indisponibles.",
        retry_policy=ReadRetryPolicy.AUTOMATIC_ONCE,
    )

    result = ReadResult.failed(
        issues=(optional_issue, required_issue),
    )

    assert result.primary_issue is required_issue
    assert required_issue.priority > optional_issue.priority


def test_erreur_interne_a_priorite_maximale():
    internal = ReadIssue(
        code=ReadIssueCode.INTERNAL_READ_ERROR,
        message="Lecture impossible.",
        source="planning",
        requirement=ReadSourceRequirement.REQUIRED,
        retry_policy=ReadRetryPolicy.USER_ACTION,
    )
    unavailable = required_source_unavailable(
        source="presences",
        message="Présences indisponibles.",
    )

    result = ReadResult.failed(
        issues=(unavailable, internal),
    )

    assert result.primary_issue is internal
    assert internal.priority > unavailable.priority


def test_donnees_invalides_requises_devancent_degradation_optionnelle():
    invalid = ReadIssue(
        code=ReadIssueCode.SOURCE_DATA_INVALID,
        message="Présences incohérentes.",
        source="presences",
        requirement=ReadSourceRequirement.REQUIRED,
    )
    optional_issue = optional_source_unavailable(
        source="holidays",
        message="Jours fériés indisponibles.",
    )

    result = ReadResult.failed(
        issues=(optional_issue, invalid),
    )

    assert result.primary_issue is invalid


def test_ordre_est_stable_a_priorite_egale():
    issue_b = optional_source_unavailable(
        source="vacations",
        message="Vacances indisponibles.",
    )
    issue_a = optional_source_unavailable(
        source="holidays",
        message="Jours fériés indisponibles.",
    )

    result = ReadResult.partial_result(
        value=DummySnapshot("dégradé"),
        issues=(issue_b, issue_a),
    )

    assert result.primary_issue is issue_a
