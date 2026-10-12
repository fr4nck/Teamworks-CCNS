from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from application.services.hr_connections.hr_case_creation import (
    HrCaseCreationRequest,
    HrCaseCreationResult,
    HrCaseCreationService,
)
from infrastructure.persistence.teamworks_hr_case_creation_repository import (
    TeamworksHrCaseCreationRepository,
)
from infrastructure.persistence.teamworks_hr_connections_repository import (
    TeamworksHrConnectionsRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
)


@dataclass(frozen=True)
class HrCaseCreationPersonOption:
    """Identité minimale affichable dans le formulaire de création."""

    identifier: str
    label: str


@dataclass(frozen=True)
class HrCaseCreationOrganizationOption:
    """Organisme déjà configuré pouvant recevoir une nouvelle démarche."""

    code: str
    label: str


@dataclass(frozen=True)
class HrCaseCreationRuntime:
    """Façade de création contrôlée sur la structure Teamworks active."""

    _structure_ref: str
    _service: HrCaseCreationService
    _profile_repository: object
    _person_reader_factory: Callable[[], object]

    def create(
        self,
        request: HrCaseCreationRequest,
        *,
        actor_ref: str | None = None,
    ) -> HrCaseCreationResult:
        return self._service.create(
            structure_ref=self._structure_ref,
            request=request,
            actor_ref=actor_ref,
            source="teamworks-ui",
        )

    def list_organizations(self) -> tuple[HrCaseCreationOrganizationOption, ...]:
        """Expose uniquement les organismes réellement configurés de la structure."""

        profiles = self._profile_repository.list_profiles(
            structure_ref=self._structure_ref,
        )
        return tuple(
            HrCaseCreationOrganizationOption(
                code=profile.organization.code,
                label=profile.organization.label,
            )
            for profile in sorted(
                profiles,
                key=lambda item: (
                    item.organization.label.casefold(),
                    item.organization.code.casefold(),
                ),
            )
        )

    def list_people(self) -> tuple[HrCaseCreationPersonOption, ...]:
        """Lit les personnes via le reader historique puis referme immédiatement sa DB."""

        reader = self._person_reader_factory()
        try:
            records = reader.lire_identites()
        finally:
            close = getattr(reader, "close", None)
            if callable(close):
                close()

        options = []
        for record in records:
            nom = (record.nom or "").strip()
            prenom = (record.prenom or "").strip()
            label = " ".join(part for part in (nom, prenom) if part)
            if not label:
                label = "Personne #%s" % record.IDpersonne
            options.append(
                HrCaseCreationPersonOption(
                    identifier=str(record.IDpersonne),
                    label=label,
                )
            )
        return tuple(options)


class HrCaseCreationRuntimeFactory:
    """Compose CRH-29/30 sans exposer la base ou l'identité de structure à l'UI."""

    def __init__(
        self,
        *,
        db_factory: Callable[[], object] | None = None,
        now_provider: Callable[[], datetime] | None = None,
        case_id_factory: Callable[[], str] | None = None,
        event_id_factory: Callable[[], str] | None = None,
        person_reader_factory: Callable[[], object] | None = None,
    ) -> None:
        self._db_factory = db_factory
        self._now_provider = now_provider
        self._case_id_factory = case_id_factory
        self._event_id_factory = event_id_factory
        self._person_reader_factory = person_reader_factory

    def _build_person_reader_factory(self) -> Callable[[], object]:
        if self._person_reader_factory is not None:
            return self._person_reader_factory

        def factory():
            from infrastructure.persistence.person_reader import PersonReader

            return PersonReader(db_factory=self._db_factory)

        return factory

    def create(self) -> HrCaseCreationRuntime:
        structure_ref = TeamworksStructureIdentityRepository(
            db_factory=self._db_factory,
        ).get_or_create_structure_ref()
        repository = TeamworksHrCaseCreationRepository(
            db_factory=self._db_factory,
        )
        profiles = TeamworksHrConnectionsRepository(
            db_factory=self._db_factory,
        )
        service = HrCaseCreationService(
            repository=repository,
            profile_repository=profiles,
            now_provider=self._now_provider,
            case_id_factory=self._case_id_factory,
            event_id_factory=self._event_id_factory,
        )
        return HrCaseCreationRuntime(
            _structure_ref=structure_ref,
            _service=service,
            _profile_repository=profiles,
            _person_reader_factory=self._build_person_reader_factory(),
        )
