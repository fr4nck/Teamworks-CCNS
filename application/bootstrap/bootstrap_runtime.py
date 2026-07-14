from __future__ import annotations

from dataclasses import dataclass

from application.bootstrap.seed_reference_data import (
    build_default_ccns_classifications,
    build_default_salary_grid_2026,
    build_default_salary_grid_version_2026,
    build_default_roles_seed,
)
from infrastructure.repositories.people_repository import PeopleRepository, LegalProfileRepository
from infrastructure.repositories.contracts_repository import ContractRepository
from infrastructure.repositories.convention_repository import (
    ClassificationRepository,
    SalaryGridRepository,
    SalaryGridLineRepository,
    SalaryGridVersionRepository,
)
from infrastructure.repositories.activity_repository import (
    SeasonRepository,
    PeriodRepository,
    ActivityRepository,
    PlaceRepository,
    TimeslotRepository,
    AssignmentRepository,
)
from infrastructure.repositories.engine_repository import (
    CalculationRuleRepository,
    CalculationResultRepository,
    AnomalyRepository,
    IndividualCounterRepository,
)
from domain.engine.default_rules import build_default_rules
from domain.engine.default_rules_ccns import build_default_ccns_rules


@dataclass(slots=True)
class RuntimeContainer:
    people: PeopleRepository
    legal_profiles: LegalProfileRepository
    contracts: ContractRepository
    classifications: ClassificationRepository
    salary_grids: SalaryGridRepository
    salary_grid_lines: SalaryGridLineRepository
    salary_grid_versions: SalaryGridVersionRepository
    seasons: SeasonRepository
    periods: PeriodRepository
    activities: ActivityRepository
    places: PlaceRepository
    timeslots: TimeslotRepository
    assignments: AssignmentRepository
    calculation_rules: CalculationRuleRepository
    calculation_results: CalculationResultRepository
    anomalies: AnomalyRepository
    individual_counters: IndividualCounterRepository


def build_runtime_container() -> RuntimeContainer:
    container = RuntimeContainer(
        people=PeopleRepository(),
        legal_profiles=LegalProfileRepository(),
        contracts=ContractRepository(),
        classifications=ClassificationRepository(),
        salary_grids=SalaryGridRepository(),
        salary_grid_lines=SalaryGridLineRepository(),
        salary_grid_versions=SalaryGridVersionRepository(),
        seasons=SeasonRepository(),
        periods=PeriodRepository(),
        activities=ActivityRepository(),
        places=PlaceRepository(),
        timeslots=TimeslotRepository(),
        assignments=AssignmentRepository(),
        calculation_rules=CalculationRuleRepository(),
        calculation_results=CalculationResultRepository(),
        anomalies=AnomalyRepository(),
        individual_counters=IndividualCounterRepository(),
    )

    for item in build_default_ccns_classifications():
        container.classifications.add(item)

    grid, lines = build_default_salary_grid_2026()
    container.salary_grids.add(grid)
    for line in lines:
        container.salary_grid_lines.add(line)
    container.salary_grid_versions.add(build_default_salary_grid_version_2026())

    for rule in build_default_rules():
        container.calculation_rules.add(rule)

    for rule in build_default_ccns_rules():
        container.calculation_rules.add(rule)

    return container
