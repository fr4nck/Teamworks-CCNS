"""Etat de sélection typé du futur espace Recrutement Qt.

Ce module reste volontairement indépendant de Qt et de la persistance. Il
formalise deux notions que l'interface wx historique mélange implicitement :

- la ligne sélectionnée, cible des actions Modifier/Supprimer ;
- le sujet affiché dans le panneau de résumé.

Les règles historiques conservées ici sont notamment :
- ``IDpersonne`` égal à ``None`` ou ``0`` signifie qu'une candidature ou un
  entretien relève encore du candidat ;
- un ``IDpersonne`` positif est prioritaire et ne doit jamais retomber vers le
  candidat s'il est introuvable ;
- ``IDemploi == 0`` est valide pour une candidature et signifie candidature
  spontanée, mais n'est jamais un identifiant d'offre sélectionnable.

Aucune écriture métier n'est effectuée dans ce module.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Union


EntityExists = Callable[[int], bool]


class RecruitmentMode(str, Enum):
    CANDIDATES = "candidats"
    APPLICATIONS = "candidatures"
    INTERVIEWS = "entretiens"
    JOBS = "emplois"


class RowKind(str, Enum):
    CANDIDATE = "candidat"
    APPLICATION = "candidature"
    INTERVIEW = "entretien"
    JOB = "emploi"


class SelectionError(str, Enum):
    MISSING_ROW_ID = "missing_row_id"
    INVALID_ROW_ID = "invalid_row_id"
    INVALID_REFERENCE_ID = "invalid_reference_id"
    NO_IDENTITY_REFERENCE = "no_identity_reference"
    CANDIDATE_NOT_FOUND = "candidate_not_found"
    PERSON_NOT_FOUND = "person_not_found"
    JOB_NOT_FOUND = "job_not_found"
    MODE_MISMATCH = "mode_mismatch"


class IntegrityWarning(str, Enum):
    CANDIDATE_REFERENCE_BROKEN = "candidate_reference_broken"
    JOB_REFERENCE_BROKEN = "job_reference_broken"


@dataclass(frozen=True)
class CandidateSubject:
    candidate_id: int

    def __post_init__(self) -> None:
        _require_positive_id(self.candidate_id)


@dataclass(frozen=True)
class PersonSubject:
    person_id: int

    def __post_init__(self) -> None:
        _require_positive_id(self.person_id)


@dataclass(frozen=True)
class JobOfferSubject:
    job_id: int

    def __post_init__(self) -> None:
        _require_positive_id(self.job_id)


RecruitmentSubject = Union[CandidateSubject, PersonSubject, JobOfferSubject]


@dataclass(frozen=True)
class SpontaneousApplication:
    """Relation explicite correspondant à ``candidatures.IDemploi == 0``."""


@dataclass(frozen=True)
class JobOfferRelation:
    job_id: int

    def __post_init__(self) -> None:
        _require_positive_id(self.job_id)


JobRelation = Union[SpontaneousApplication, JobOfferRelation]


@dataclass(frozen=True)
class CandidateSelection:
    candidate_id: int

    @property
    def row_id(self) -> int:
        return self.candidate_id

    @property
    def subject(self) -> CandidateSubject:
        return CandidateSubject(self.candidate_id)

    @property
    def row_kind(self) -> RowKind:
        return RowKind.CANDIDATE

    @property
    def mode(self) -> RecruitmentMode:
        return RecruitmentMode.CANDIDATES


@dataclass(frozen=True)
class ApplicationSelection:
    application_id: int
    candidate_id: Optional[int]
    person_id: Optional[int]
    job_relation: JobRelation
    summary_subject: Union[CandidateSubject, PersonSubject]

    @property
    def row_id(self) -> int:
        return self.application_id

    @property
    def subject(self) -> Union[CandidateSubject, PersonSubject]:
        return self.summary_subject

    @property
    def row_kind(self) -> RowKind:
        return RowKind.APPLICATION

    @property
    def mode(self) -> RecruitmentMode:
        return RecruitmentMode.APPLICATIONS


@dataclass(frozen=True)
class InterviewSelection:
    interview_id: int
    candidate_id: Optional[int]
    person_id: Optional[int]
    summary_subject: Union[CandidateSubject, PersonSubject]

    @property
    def row_id(self) -> int:
        return self.interview_id

    @property
    def subject(self) -> Union[CandidateSubject, PersonSubject]:
        return self.summary_subject

    @property
    def row_kind(self) -> RowKind:
        return RowKind.INTERVIEW

    @property
    def mode(self) -> RecruitmentMode:
        return RecruitmentMode.INTERVIEWS


@dataclass(frozen=True)
class JobSelection:
    job_id: int

    @property
    def row_id(self) -> int:
        return self.job_id

    @property
    def subject(self) -> JobOfferSubject:
        return JobOfferSubject(self.job_id)

    @property
    def row_kind(self) -> RowKind:
        return RowKind.JOB

    @property
    def mode(self) -> RecruitmentMode:
        return RecruitmentMode.JOBS


RecruitmentSelection = Union[
    CandidateSelection,
    ApplicationSelection,
    InterviewSelection,
    JobSelection,
]


@dataclass(frozen=True)
class SelectionResolution:
    selection: Optional[RecruitmentSelection]
    error: Optional[SelectionError] = None
    warnings: tuple[IntegrityWarning, ...] = ()

    @property
    def ok(self) -> bool:
        return self.selection is not None and self.error is None


@dataclass(frozen=True)
class ActionTarget:
    kind: RowKind
    row_id: int


class RecruitmentUiState:
    """Machine d'état minimale pour le futur contrôleur Recrutement Qt."""

    def __init__(self, mode: RecruitmentMode = RecruitmentMode.CANDIDATES) -> None:
        self.mode = mode
        self.selection: Optional[RecruitmentSelection] = None
        self.revision = 0

    def change_mode(self, mode: RecruitmentMode) -> None:
        if mode == self.mode:
            return
        self.mode = mode
        self.selection = None
        self.revision += 1

    def set_selection(self, selection: RecruitmentSelection) -> int:
        if selection.mode != self.mode:
            raise ValueError(SelectionError.MODE_MISMATCH.value)
        self.selection = selection
        self.revision += 1
        return self.revision

    def clear_selection(self) -> None:
        if self.selection is None:
            return
        self.selection = None
        self.revision += 1

    def action_target(self) -> Optional[ActionTarget]:
        if self.selection is None:
            return None
        return ActionTarget(self.selection.row_kind, self.selection.row_id)

    def accepts_response(self, revision: int, subject: RecruitmentSubject) -> bool:
        """Refuse une réponse asynchrone devenue obsolète."""

        if revision != self.revision or self.selection is None:
            return False
        return self.selection.subject == subject


def resolve_candidate_selection(
    candidate_id: object,
    *,
    candidate_exists: Optional[EntityExists] = None,
) -> SelectionResolution:
    row_id_error = _validate_required_row_id(candidate_id)
    if row_id_error is not None:
        return SelectionResolution(None, row_id_error)
    candidate_id = int(candidate_id)
    if candidate_exists is not None and not candidate_exists(candidate_id):
        return SelectionResolution(None, SelectionError.CANDIDATE_NOT_FOUND)
    return SelectionResolution(CandidateSelection(candidate_id))


def resolve_application_selection(
    application_id: object,
    *,
    candidate_id: object,
    person_id: object,
    job_id: object,
    candidate_exists: Optional[EntityExists] = None,
    person_exists: Optional[EntityExists] = None,
    job_exists: Optional[EntityExists] = None,
) -> SelectionResolution:
    row_id_error = _validate_required_row_id(application_id)
    if row_id_error is not None:
        return SelectionResolution(None, row_id_error)
    application_id = int(application_id)

    person_state = _legacy_optional_id(person_id)
    candidate_state = _legacy_optional_id(candidate_id)

    if person_state.invalid or candidate_state.invalid:
        return SelectionResolution(None, SelectionError.INVALID_REFERENCE_ID)

    warnings: list[IntegrityWarning] = []

    if person_state.value is not None:
        resolved_person_id = person_state.value
        if person_exists is not None and not person_exists(resolved_person_id):
            return SelectionResolution(None, SelectionError.PERSON_NOT_FOUND)
        subject: Union[CandidateSubject, PersonSubject] = PersonSubject(resolved_person_id)
        if (
            candidate_state.value is not None
            and candidate_exists is not None
            and not candidate_exists(candidate_state.value)
        ):
            warnings.append(IntegrityWarning.CANDIDATE_REFERENCE_BROKEN)
    else:
        if candidate_state.value is None:
            return SelectionResolution(None, SelectionError.NO_IDENTITY_REFERENCE)
        resolved_candidate_id = candidate_state.value
        if candidate_exists is not None and not candidate_exists(resolved_candidate_id):
            return SelectionResolution(None, SelectionError.CANDIDATE_NOT_FOUND)
        subject = CandidateSubject(resolved_candidate_id)

    job_relation, job_warning, job_error = _resolve_job_relation(job_id, job_exists)
    if job_error is not None:
        return SelectionResolution(None, job_error)
    if job_warning is not None:
        warnings.append(job_warning)

    selection = ApplicationSelection(
        application_id=application_id,
        candidate_id=candidate_state.value,
        person_id=person_state.value,
        job_relation=job_relation,
        summary_subject=subject,
    )
    return SelectionResolution(selection, warnings=tuple(warnings))


def resolve_interview_selection(
    interview_id: object,
    *,
    candidate_id: object,
    person_id: object,
    candidate_exists: Optional[EntityExists] = None,
    person_exists: Optional[EntityExists] = None,
) -> SelectionResolution:
    row_id_error = _validate_required_row_id(interview_id)
    if row_id_error is not None:
        return SelectionResolution(None, row_id_error)
    interview_id = int(interview_id)

    person_state = _legacy_optional_id(person_id)
    candidate_state = _legacy_optional_id(candidate_id)
    if person_state.invalid or candidate_state.invalid:
        return SelectionResolution(None, SelectionError.INVALID_REFERENCE_ID)

    warnings: list[IntegrityWarning] = []
    if person_state.value is not None:
        resolved_person_id = person_state.value
        if person_exists is not None and not person_exists(resolved_person_id):
            return SelectionResolution(None, SelectionError.PERSON_NOT_FOUND)
        subject: Union[CandidateSubject, PersonSubject] = PersonSubject(resolved_person_id)
        if (
            candidate_state.value is not None
            and candidate_exists is not None
            and not candidate_exists(candidate_state.value)
        ):
            warnings.append(IntegrityWarning.CANDIDATE_REFERENCE_BROKEN)
    else:
        if candidate_state.value is None:
            return SelectionResolution(None, SelectionError.NO_IDENTITY_REFERENCE)
        resolved_candidate_id = candidate_state.value
        if candidate_exists is not None and not candidate_exists(resolved_candidate_id):
            return SelectionResolution(None, SelectionError.CANDIDATE_NOT_FOUND)
        subject = CandidateSubject(resolved_candidate_id)

    selection = InterviewSelection(
        interview_id=interview_id,
        candidate_id=candidate_state.value,
        person_id=person_state.value,
        summary_subject=subject,
    )
    return SelectionResolution(selection, warnings=tuple(warnings))


def resolve_job_selection(
    job_id: object,
    *,
    job_exists: Optional[EntityExists] = None,
) -> SelectionResolution:
    row_id_error = _validate_required_row_id(job_id)
    if row_id_error is not None:
        return SelectionResolution(None, row_id_error)
    job_id = int(job_id)
    if job_exists is not None and not job_exists(job_id):
        return SelectionResolution(None, SelectionError.JOB_NOT_FOUND)
    return SelectionResolution(JobSelection(job_id))


def application_matches_subject(
    selection: ApplicationSelection,
    subject: RecruitmentSubject,
) -> bool:
    if isinstance(subject, PersonSubject):
        return selection.person_id == subject.person_id
    if isinstance(subject, CandidateSubject):
        return selection.person_id is None and selection.candidate_id == subject.candidate_id
    if isinstance(subject, JobOfferSubject):
        relation = selection.job_relation
        return isinstance(relation, JobOfferRelation) and relation.job_id == subject.job_id
    return False


def interview_matches_subject(
    selection: InterviewSelection,
    subject: RecruitmentSubject,
) -> bool:
    if isinstance(subject, PersonSubject):
        return selection.person_id == subject.person_id
    if isinstance(subject, CandidateSubject):
        return selection.person_id is None and selection.candidate_id == subject.candidate_id
    return False


def _resolve_job_relation(
    job_id: object,
    job_exists: Optional[EntityExists],
) -> tuple[JobRelation, Optional[IntegrityWarning], Optional[SelectionError]]:
    if isinstance(job_id, bool) or not isinstance(job_id, int):
        return SpontaneousApplication(), None, SelectionError.INVALID_REFERENCE_ID
    if job_id < 0:
        return SpontaneousApplication(), None, SelectionError.INVALID_REFERENCE_ID
    if job_id == 0:
        return SpontaneousApplication(), None, None
    if job_exists is not None and not job_exists(job_id):
        return JobOfferRelation(job_id), IntegrityWarning.JOB_REFERENCE_BROKEN, None
    return JobOfferRelation(job_id), None, None


@dataclass(frozen=True)
class _OptionalLegacyId:
    value: Optional[int]
    invalid: bool = False


def _legacy_optional_id(value: object) -> _OptionalLegacyId:
    if value is None or value == 0:
        if isinstance(value, bool):
            return _OptionalLegacyId(None, invalid=True)
        return _OptionalLegacyId(None)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return _OptionalLegacyId(None, invalid=True)
    return _OptionalLegacyId(value)


def _validate_required_row_id(value: object) -> Optional[SelectionError]:
    if value is None:
        return SelectionError.MISSING_ROW_ID
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return SelectionError.INVALID_ROW_ID
    return None


def _require_positive_id(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("identifier must be a positive integer")
