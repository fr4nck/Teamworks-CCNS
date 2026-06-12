from __future__ import annotations

from datetime import date

from domain.convention.classification import CCNSClassification
from domain.convention.salary_grid import SalaryGrid
from domain.convention.salary_grid_line import SalaryGridLine
from domain.convention.minimum_type import MinimumType
from domain.activity.time_nature import TimeNature
from domain.security.default_roles import build_default_roles


def build_default_ccns_classifications() -> list[CCNSClassification]:
    today = date(2026, 1, 1)
    return [
        CCNSClassification(code="G1", label="Groupe 1", effective_date=today),
        CCNSClassification(code="G2", label="Groupe 2", effective_date=today),
        CCNSClassification(code="G3", label="Groupe 3", effective_date=today),
        CCNSClassification(code="G4", label="Groupe 4", effective_date=today),
        CCNSClassification(code="G5", label="Groupe 5", effective_date=today),
        CCNSClassification(code="G6", label="Groupe 6", effective_date=today),
        CCNSClassification(code="G7", label="Groupe 7", effective_date=today),
        CCNSClassification(code="G8", label="Groupe 8", effective_date=today),
        CCNSClassification(code="APPRENTI", label="Apprenti", effective_date=today),
    ]


def build_default_salary_grid_2026() -> tuple[SalaryGrid, list[SalaryGridLine]]:
    grid = SalaryGrid(
        code="CCNS-2026",
        label="CCNS 2026",
        effective_date=date(2026, 1, 1),
        source_reference="Bootstrap Teamworks-CCNS",
    )
    lines = [
        SalaryGridLine(
            salary_grid_id=grid.id,
            classification_code="G1",
            minimum_type=MinimumType.MONTHLY,
            amount=1801.84,
            unit="EUR",
        ),
        SalaryGridLine(
            salary_grid_id=grid.id,
            classification_code="G2",
            minimum_type=MinimumType.MONTHLY,
            amount=1888.93,
            unit="EUR",
        ),
        SalaryGridLine(
            salary_grid_id=grid.id,
            classification_code="G3",
            minimum_type=MinimumType.MONTHLY,
            amount=1997.87,
            unit="EUR",
        ),
        SalaryGridLine(
            salary_grid_id=grid.id,
            classification_code="G4",
            minimum_type=MinimumType.MONTHLY,
            amount=2138.43,
            unit="EUR",
        ),
        SalaryGridLine(
            salary_grid_id=grid.id,
            classification_code="G5",
            minimum_type=MinimumType.MONTHLY,
            amount=2353.79,
            unit="EUR",
        ),
        SalaryGridLine(
            salary_grid_id=grid.id,
            classification_code="G6",
            minimum_type=MinimumType.MONTHLY,
            amount=2736.28,
            unit="EUR",
        ),
        SalaryGridLine(
            salary_grid_id=grid.id,
            classification_code="G7",
            minimum_type=MinimumType.ANNUAL,
            amount=40597.94,
            unit="EUR",
        ),
        SalaryGridLine(
            salary_grid_id=grid.id,
            classification_code="G8",
            minimum_type=MinimumType.ANNUAL,
            amount=53577.30,
            unit="EUR",
        ),
        SalaryGridLine(
            salary_grid_id=grid.id,
            classification_code="APPRENTI",
            minimum_type=MinimumType.MONTHLY,
            amount=800.00,
            unit="EUR",
            age_min=18,
            age_max=20,
            execution_year_min=2,
            execution_year_max=2,
        ),
    ]
    return grid, lines


def build_default_time_natures() -> list[dict[str, str]]:
    return [
        {"code": TimeNature.FACE_PUBLIC.value, "label": "Face public"},
        {"code": TimeNature.PREPARATION.value, "label": "Préparation"},
        {"code": TimeNature.TRAVEL.value, "label": "Déplacement"},
        {"code": TimeNature.COORDINATION.value, "label": "Coordination"},
        {"code": TimeNature.MEETING.value, "label": "Réunion"},
        {"code": TimeNature.ADMINISTRATIVE.value, "label": "Administratif"},
        {"code": TimeNature.STAGE_OBSERVATION.value, "label": "Observation stage"},
        {"code": TimeNature.VOLUNTEER.value, "label": "Bénévolat"},
    ]


def build_default_roles_seed():
    return build_default_roles()
