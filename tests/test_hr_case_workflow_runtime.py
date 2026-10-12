import sqlite3
from datetime import date, datetime, timezone

from application.bootstrap import HrCaseWorkflowRuntimeFactory
from domain.hr_connections import (
    HrCase,
    HrCaseStatus,
    HrCaseSubject,
    HrCaseSubjectKind,
    HrCaseType,
)
from infrastructure.persistence import (
    TeamworksHrCasesRepository,
    TeamworksStructureIdentityRepository,
)


class LocalGestionDb:
    def __init__(self, path):
        self.isNetwork = False
        self.connexion = sqlite3.connect(path)
        self.cursor = self.connexion.cursor()

    def Commit(self):
        self.connexion.commit()

    def Close(self):
        self.connexion.close()


def _factory(path):
    return lambda: LocalGestionDb(path)


def _case():
    return HrCase(
        case_id="case-1",
        case_type=HrCaseType.create(code="dpae", label="DPAE"),
        subject=HrCaseSubject.create(
            kind=HrCaseSubjectKind.PERSON,
            identifier="42",
        ),
        organization_code="urssaf",
        opened_on=date(2026, 9, 1),
        due_on=date(2026, 9, 3),
    )


def test_runtime_hides_structure_identity_and_applies_atomic_transition(tmp_path):
    path = tmp_path / "workflow-runtime.sqlite"
    factory = _factory(path)
    structure_ref = TeamworksStructureIdentityRepository(
        db_factory=factory
    ).get_or_create_structure_ref()
    cases = TeamworksHrCasesRepository(db_factory=factory)
    cases.save_case(structure_ref=structure_ref, case=_case())

    runtime = HrCaseWorkflowRuntimeFactory(
        db_factory=factory,
        now_provider=lambda: datetime(2026, 9, 1, 20, 0, tzinfo=timezone.utc),
        event_id_factory=lambda: "evt-runtime-1",
    ).create()

    assert not hasattr(runtime, "structure_ref")
    assert runtime.available_transitions(case_id="case-1").allowed_statuses == (
        HrCaseStatus.PREPARED,
        HrCaseStatus.CANCELLED,
    )

    result = runtime.transition(
        case_id="case-1",
        status=HrCaseStatus.PREPARED,
        actor_ref="user-1",
        comment="Prêt",
    )

    assert result.case.status is HrCaseStatus.PREPARED
    assert cases.get_case(
        structure_ref=structure_ref,
        case_id="case-1",
    ).status is HrCaseStatus.PREPARED
    assert cases.get_event(
        structure_ref=structure_ref,
        event_id="evt-runtime-1",
    ) == result.event
