from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

_CENT = Decimal("0.01")
_LEGAL_WEEKLY_HOURS = Decimal("35.00")
_NO_SMIC_VERSION = "Aucune version du SMIC n’est applicable à la date et au territoire demandés."


class SmicTerritory(str, Enum):
    METROPOLITAN_FRANCE = "metropolitan_france"
    MAYOTTE = "mayotte"


def _strict_date(value: object, field_name: str) -> date:
    if type(value) is not date:
        raise TypeError(f"{field_name} doit être une date stricte.")
    return value


def _strict_decimal(value: object, field_name: str) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} doit être un Decimal strict.")
    if value <= Decimal("0"):
        raise ValueError(f"{field_name} doit être strictement supérieur à zéro.")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    """Quantifie indépendamment du contexte Decimal laissé par le runtime historique."""
    with localcontext() as context:
        context.prec = max(28, len(value.as_tuple().digits) + 4)
        return value.quantize(_CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True)
class SmicVersion:
    code: str
    name: str
    territory: SmicTerritory
    effective_from: date
    effective_until: Optional[date]
    hourly_gross_amount: Decimal
    monthly_gross_amount_35h: Decimal
    legal_weekly_hours: Decimal
    source_reference: str
    active: bool = True
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.code) is not str or not self.code.strip():
            raise ValueError("code est obligatoire.")
        if type(self.name) is not str or not self.name.strip():
            raise ValueError("name est obligatoire.")
        if type(self.territory) is not SmicTerritory:
            raise TypeError("territory doit être un SmicTerritory.")
        effective_from = _strict_date(self.effective_from, "effective_from")
        effective_until = self.effective_until
        if effective_until is not None:
            effective_until = _strict_date(effective_until, "effective_until")
            if effective_until < effective_from:
                raise ValueError("effective_until doit être supérieure ou égale à effective_from.")
        hourly = _strict_decimal(self.hourly_gross_amount, "hourly_gross_amount")
        monthly = _strict_decimal(self.monthly_gross_amount_35h, "monthly_gross_amount_35h")
        weekly_hours = _strict_decimal(self.legal_weekly_hours, "legal_weekly_hours")
        if type(self.source_reference) is not str or not self.source_reference.strip():
            raise ValueError("source_reference est obligatoire.")
        if type(self.active) is not bool:
            raise TypeError("active doit être un booléen strict.")
        if type(self.id) is not UUID:
            raise TypeError("id doit être un UUID strict.")

        object.__setattr__(self, "code", self.code.strip().upper())
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "effective_from", effective_from)
        object.__setattr__(self, "effective_until", effective_until)
        object.__setattr__(self, "hourly_gross_amount", _quantize_decimal(hourly))
        object.__setattr__(self, "monthly_gross_amount_35h", _quantize_decimal(monthly))
        object.__setattr__(self, "legal_weekly_hours", _quantize_decimal(weekly_hours))
        object.__setattr__(self, "source_reference", self.source_reference.strip())

    def is_active(self) -> bool:
        return self.active

    def is_open_ended(self) -> bool:
        return self.effective_until is None

    def applies_on(self, reference_date: date) -> bool:
        reference_date = _strict_date(reference_date, "reference_date")
        return reference_date >= self.effective_from and (
            self.effective_until is None or reference_date <= self.effective_until
        )

    def is_metropolitan(self) -> bool:
        return self.territory is SmicTerritory.METROPOLITAN_FRANCE

    def is_mayotte(self) -> bool:
        return self.territory is SmicTerritory.MAYOTTE


@dataclass(frozen=True, slots=True)
class SmicCatalog:
    versions: tuple[SmicVersion, ...]
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.id) is not UUID:
            raise TypeError("id doit être un UUID strict.")
        if type(self.versions) is not tuple:
            raise TypeError("versions doit être un tuple non vide.")
        if not self.versions:
            raise ValueError("versions doit être un tuple non vide.")
        if any(type(version) is not SmicVersion for version in self.versions):
            raise TypeError("Chaque version doit être un SmicVersion.")
        if len({version.id for version in self.versions}) != len(self.versions):
            raise ValueError("Les UUID des versions doivent être uniques.")
        if len({version.code for version in self.versions}) != len(self.versions):
            raise ValueError("Les codes des versions doivent être uniques.")
        for index, left in enumerate(self.versions):
            for right in self.versions[index + 1:]:
                if left.territory is right.territory and self._overlap(left, right):
                    raise ValueError("Les périodes d’application du SMIC ne doivent pas se chevaucher pour un même territoire.")

    @staticmethod
    def _overlap(left: SmicVersion, right: SmicVersion) -> bool:
        return (left.effective_until is None or left.effective_until >= right.effective_from) and (
            right.effective_until is None or right.effective_until >= left.effective_from
        )

    def version_count(self) -> int:
        return len(self.versions)

    def version_applicable_on(self, reference_date: date, territory: SmicTerritory) -> SmicVersion:
        reference_date = _strict_date(reference_date, "reference_date")
        if type(territory) is not SmicTerritory:
            raise TypeError("territory doit être un SmicTerritory.")
        for version in self.versions:
            if version.territory is territory and version.applies_on(reference_date):
                return version
        raise ValueError(_NO_SMIC_VERSION)

    def hourly_amount_on(self, reference_date: date, territory: SmicTerritory) -> Decimal:
        return self.version_applicable_on(reference_date, territory).hourly_gross_amount

    def monthly_amount_35h_on(self, reference_date: date, territory: SmicTerritory) -> Decimal:
        return self.version_applicable_on(reference_date, territory).monthly_gross_amount_35h

    def has_version_for(self, reference_date: date, territory: SmicTerritory) -> bool:
        reference_date = _strict_date(reference_date, "reference_date")
        if type(territory) is not SmicTerritory:
            raise TypeError("territory doit être un SmicTerritory.")
        return any(version.territory is territory and version.applies_on(reference_date) for version in self.versions)


def create_metropolitan_smic_2026_01() -> SmicVersion:
    return SmicVersion(
        code="SMIC-METROPOLE-2026-01",
        name="SMIC métropole janvier 2026",
        territory=SmicTerritory.METROPOLITAN_FRANCE,
        effective_from=date(2026, 1, 1),
        effective_until=date(2026, 5, 31),
        hourly_gross_amount=Decimal("12.02"),
        monthly_gross_amount_35h=Decimal("1823.03"),
        legal_weekly_hours=_LEGAL_WEEKLY_HOURS,
        source_reference="Décret n° 2025-1228 du 17 décembre 2025, applicable au 1er janvier 2026",
    )


def create_mayotte_smic_2026_01() -> SmicVersion:
    return SmicVersion(
        code="SMIC-MAYOTTE-2026-01",
        name="SMIC Mayotte janvier 2026",
        territory=SmicTerritory.MAYOTTE,
        effective_from=date(2026, 1, 1),
        effective_until=date(2026, 5, 31),
        hourly_gross_amount=Decimal("9.33"),
        monthly_gross_amount_35h=Decimal("1415.05"),
        legal_weekly_hours=_LEGAL_WEEKLY_HOURS,
        source_reference="Décret n° 2025-1228 du 17 décembre 2025, applicable au 1er janvier 2026",
    )


def create_metropolitan_smic_2026_06() -> SmicVersion:
    return SmicVersion(
        code="SMIC-METROPOLE-2026-06",
        name="SMIC métropole juin 2026",
        territory=SmicTerritory.METROPOLITAN_FRANCE,
        effective_from=date(2026, 6, 1),
        effective_until=None,
        hourly_gross_amount=Decimal("12.31"),
        monthly_gross_amount_35h=Decimal("1867.02"),
        legal_weekly_hours=_LEGAL_WEEKLY_HOURS,
        source_reference="Arrêté du 22 mai 2026, applicable au 1er juin 2026",
    )


def create_mayotte_smic_2026_06() -> SmicVersion:
    return SmicVersion(
        code="SMIC-MAYOTTE-2026-06",
        name="SMIC Mayotte juin 2026",
        territory=SmicTerritory.MAYOTTE,
        effective_from=date(2026, 6, 1),
        effective_until=None,
        hourly_gross_amount=Decimal("9.56"),
        monthly_gross_amount_35h=Decimal("1449.93"),
        legal_weekly_hours=_LEGAL_WEEKLY_HOURS,
        source_reference="Arrêté du 22 mai 2026, applicable au 1er juin 2026",
    )


def create_smic_catalog_2026() -> SmicCatalog:
    return SmicCatalog(
        (
            create_metropolitan_smic_2026_01(),
            create_mayotte_smic_2026_01(),
            create_metropolitan_smic_2026_06(),
            create_mayotte_smic_2026_06(),
        )
    )
