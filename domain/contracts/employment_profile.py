"""Profil métier immutable décrivant le régime applicable à un emploi."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .employment_regime import EmploymentRegime


@dataclass(frozen=True, slots=True)
class EmploymentProfile:
    """Régime métier applicable à un emploi, indépendamment du contrat.

    Cet objet ne porte ni données personnelles, ni données contractuelles,
    salariales ou de planification. Ses indicateurs expriment seulement les
    contrôles métier auxquels le régime est soumis.
    """

    id: UUID = field(default_factory=uuid4, kw_only=True)
    name: str
    regime: EmploymentRegime
    subject_to_ccns: bool
    subject_to_salary_grid: bool
    subject_to_working_time_controls: bool
    subject_to_cee_controls: bool
    active: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("L'identifiant du profil d'emploi doit être un UUID.")
        if not isinstance(self.name, str) or not (name := self.name.strip()):
            raise ValueError("Le nom du profil d'emploi est obligatoire.")
        if not isinstance(self.regime, EmploymentRegime):
            raise ValueError("Le régime d'emploi du profil est invalide.")

        for value, field_name in (
            (self.subject_to_ccns, "soumission à la CCNS"),
            (self.subject_to_salary_grid, "soumission à la grille salariale"),
            (self.subject_to_working_time_controls, "soumission aux contrôles du temps de travail"),
            (self.subject_to_cee_controls, "soumission aux contrôles CEE"),
            (self.active, "statut actif"),
        ):
            if not isinstance(value, bool):
                raise ValueError(f"La {field_name} doit être un booléen.")

        object.__setattr__(self, "name", name)

    def is_ccns(self) -> bool:
        """Indique si le profil est soumis à la CCNS."""
        return self.subject_to_ccns

    def requires_salary_grid(self) -> bool:
        """Indique si le profil relève de la grille salariale."""
        return self.subject_to_salary_grid

    def requires_working_time_controls(self) -> bool:
        """Indique si le profil requiert les contrôles du temps de travail."""
        return self.subject_to_working_time_controls

    def requires_cee_controls(self) -> bool:
        """Indique si le profil requiert les contrôles propres au CEE."""
        return self.subject_to_cee_controls
