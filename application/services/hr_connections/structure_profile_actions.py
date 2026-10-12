from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Tuple

from domain.hr_connections import (
    ConnectionProfile,
    EffectivePeriod,
    HrOrganization,
    OrganizationKind,
    OrganizationReference,
    PortalLink,
)


@dataclass(frozen=True)
class StructureConnectionProfileRequest:
    """Données modifiables d'un organisme sans exposer l'identité de structure.

    Les capacités d'intégration ne sont volontairement pas saisies ici : elles
    décrivent un connecteur réellement disponible et ne doivent pas devenir des
    cases déclaratives permettant d'annoncer une API ou une synchronisation qui
    n'existe pas.
    """

    organization_code: str
    organization_label: str
    organization_kind: OrganizationKind
    references: Tuple[OrganizationReference, ...] = ()
    portal_links: Tuple[PortalLink, ...] = ()
    starts_on: date | None = None
    ends_on: date | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.organization_code, str) or not self.organization_code.strip():
            raise ValueError("Le code stable de l'organisme est obligatoire.")
        if not isinstance(self.organization_label, str) or not self.organization_label.strip():
            raise ValueError("Le libellé de l'organisme est obligatoire.")
        if not isinstance(self.organization_kind, OrganizationKind):
            raise TypeError("La famille d'organisme est invalide.")
        if any(not isinstance(item, OrganizationReference) for item in self.references):
            raise TypeError("Une référence d'organisme est invalide.")
        if any(not isinstance(item, PortalLink) for item in self.portal_links):
            raise TypeError("Un lien de portail est invalide.")
        for label, value in (
            ("date d'effet", self.starts_on),
            ("date de fin", self.ends_on),
        ):
            if value is not None and not isinstance(value, date):
                raise TypeError(f"La {label} de l'organisme est invalide.")
        EffectivePeriod(starts_on=self.starts_on, ends_on=self.ends_on)

        reference_keys = [
            (item.reference_type, item.value)
            for item in self.references
        ]
        if len(reference_keys) != len(set(reference_keys)):
            raise ValueError("Une même référence d'organisme ne peut pas être saisie deux fois.")
        portal_keys = [item.url for item in self.portal_links]
        if len(portal_keys) != len(set(portal_keys)):
            raise ValueError("Une même URL de portail ne peut pas être saisie deux fois.")

    @classmethod
    def create(
        cls,
        *,
        organization_code: str,
        organization_label: str,
        organization_kind: OrganizationKind,
        references: Iterable[OrganizationReference] = (),
        portal_links: Iterable[PortalLink] = (),
        starts_on: date | None = None,
        ends_on: date | None = None,
    ) -> "StructureConnectionProfileRequest":
        return cls(
            organization_code=organization_code.strip(),
            organization_label=organization_label.strip(),
            organization_kind=organization_kind,
            references=tuple(references),
            portal_links=tuple(portal_links),
            starts_on=starts_on,
            ends_on=ends_on,
        )

    def to_profile(
        self,
        *,
        structure_ref: str,
        capabilities=(),
    ) -> ConnectionProfile:
        if not isinstance(structure_ref, str) or not structure_ref.strip():
            raise ValueError("La référence de structure est obligatoire.")
        period = None
        if self.starts_on is not None or self.ends_on is not None:
            period = EffectivePeriod(starts_on=self.starts_on, ends_on=self.ends_on)
        return ConnectionProfile.create(
            structure_ref=structure_ref,
            organization=HrOrganization.create(
                code=self.organization_code,
                label=self.organization_label,
                kind=self.organization_kind,
            ),
            capabilities=capabilities,
            references=self.references,
            portal_links=self.portal_links,
            effective_period=period,
        )
