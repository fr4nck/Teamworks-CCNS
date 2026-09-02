import sqlite3
from datetime import date
from pathlib import Path

from application.bootstrap.hr_lifecycle_planning_factory import (
    HrLifecyclePlanningRuntimeFactory,
)
from domain.hr_connections import (
    ConnectionProfile,
    ExpectedDocument,
    HrCaseType,
    HrLifecycleEvent,
    HrLifecycleEventKind,
    HrLifecycleTemplate,
    HrOrganization,
    OrganizationKind,
)
from infrastructure.persistence.teamworks_hr_connections_repository import (
    TeamworksHrConnectionsRepository,
)
from infrastructure.persistence.teamworks_hr_lifecycle_template_repository import (
    TeamworksHrLifecycleTemplateRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
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


def _template(
    template_id="start-local",
    *,
    kind=HrLifecycleEventKind.EMPLOYMENT_START,
    organization_code="urssaf",
    due_offset_days=2,
    enabled=True,
    documents=None,
):
    if documents is None:
        documents = (
            ExpectedDocument.create(
                code="piece-a",
                label="Pièce A",
                required=True,
            ),
            ExpectedDocument.create(
                code="piece-b",
                label="Pièce B",
                required=False,
            ),
        )
    return HrLifecycleTemplate.create(
        template_id=template_id,
        event_kind=kind,
        organization_code=organization_code,
        case_type=HrCaseType.create(code="local-case", label="Démarche locale"),
        due_offset_days=due_offset_days,
        expected_documents=documents,
        enabled=enabled,
    )


def test_schema_is_additive_versioned_and_autonomous(tmp_path):
    path = tmp_path / "lifecycle.sqlite"
    factory = _factory(path)
    repository = TeamworksHrLifecycleTemplateRepository(db_factory=factory)

    assert repository.schema_version() == 1
    repository.ensure_schema()
    assert repository.schema_version() == 1

    db = factory()
    try:
        tables = {
            row[0]
            for row in db.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        indexes = {
            row[0]
            for row in db.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }
    finally:
        db.Close()

    assert "tw_hr_schema_versions" in tables
    assert "tw_hr_lifecycle_templates" in tables
    assert "tw_hr_lifecycle_template_documents" in tables
    assert "idx_tw_hr_lifecycle_event" in indexes
    assert "idx_tw_hr_lifecycle_org" in indexes


def test_template_round_trip_preserves_explicit_configuration_and_document_order(tmp_path):
    path = tmp_path / "lifecycle.sqlite"
    repository = TeamworksHrLifecycleTemplateRepository(db_factory=_factory(path))
    template = _template()

    assert repository.save_template(
        structure_ref="structure-a",
        template=template,
    ) == template

    loaded = repository.get_template(
        structure_ref="structure-a",
        template_id="start-local",
    )
    assert loaded == template
    assert [item.code for item in loaded.expected_documents] == ["piece-a", "piece-b"]
    assert loaded.expected_documents[0].required is True
    assert loaded.expected_documents[1].required is False


def test_update_replaces_current_configuration_without_leaving_stale_documents(tmp_path):
    path = tmp_path / "lifecycle.sqlite"
    repository = TeamworksHrLifecycleTemplateRepository(db_factory=_factory(path))
    repository.save_template(structure_ref="structure-a", template=_template())

    updated = _template(
        due_offset_days=None,
        enabled=False,
        documents=(
            ExpectedDocument.create(
                code="new-piece",
                label="Nouvelle pièce",
                required=False,
            ),
        ),
    )
    repository.save_template(structure_ref="structure-a", template=updated)

    loaded = repository.get_template(
        structure_ref="structure-a",
        template_id="start-local",
    )
    assert loaded == updated
    assert loaded.due_offset_days is None
    assert loaded.enabled is False
    assert [item.code for item in loaded.expected_documents] == ["new-piece"]


def test_list_is_filtered_by_structure_and_event_kind_and_loads_documents_in_group(tmp_path):
    path = tmp_path / "lifecycle.sqlite"
    repository = TeamworksHrLifecycleTemplateRepository(db_factory=_factory(path))
    repository.save_template(structure_ref="structure-a", template=_template("start-b"))
    repository.save_template(structure_ref="structure-a", template=_template("start-a"))
    repository.save_template(
        structure_ref="structure-a",
        template=_template("end-a", kind=HrLifecycleEventKind.EMPLOYMENT_END),
    )
    repository.save_template(structure_ref="structure-b", template=_template("other"))

    listed = repository.list_templates(
        structure_ref="structure-a",
        event_kind=HrLifecycleEventKind.EMPLOYMENT_START,
    )

    assert [item.template_id for item in listed] == ["start-a", "start-b"]
    assert all(len(item.expected_documents) == 2 for item in listed)


def test_disabling_template_is_persisted_instead_of_deleting_configuration(tmp_path):
    path = tmp_path / "lifecycle.sqlite"
    factory = _factory(path)
    repository = TeamworksHrLifecycleTemplateRepository(db_factory=factory)
    repository.save_template(
        structure_ref="structure-a",
        template=_template(enabled=False),
    )

    db = factory()
    try:
        row = db.cursor.execute(
            "SELECT enabled FROM tw_hr_lifecycle_templates "
            "WHERE structure_ref = ? AND template_id = ?",
            ("structure-a", "start-local"),
        ).fetchone()
    finally:
        db.Close()

    assert row == (0,)
    assert repository.get_template(
        structure_ref="structure-a",
        template_id="start-local",
    ).enabled is False


def test_runtime_uses_stable_structure_identity_and_active_database(tmp_path):
    path = tmp_path / "lifecycle-runtime.sqlite"
    factory = _factory(path)
    identity = TeamworksStructureIdentityRepository(db_factory=factory)
    structure_ref = identity.get_or_create_structure_ref()

    profiles = TeamworksHrConnectionsRepository(db_factory=factory)
    profiles.save_profile(
        ConnectionProfile.create(
            structure_ref=structure_ref,
            organization=HrOrganization.create(
                code="urssaf",
                label="Organisme configuré",
                kind=OrganizationKind.URSSAF,
            ),
        )
    )
    templates = TeamworksHrLifecycleTemplateRepository(db_factory=factory)
    templates.save_template(structure_ref=structure_ref, template=_template())

    runtime = HrLifecyclePlanningRuntimeFactory(db_factory=factory).create()
    plan = runtime.plan(
        event=HrLifecycleEvent.create(
            event_id="event-1",
            kind=HrLifecycleEventKind.EMPLOYMENT_START,
            person_ref="42",
            effective_on=date(2026, 9, 7),
        )
    )

    assert plan.structure_ref == structure_ref
    assert plan.suggestion_count == 1
    assert plan.suggestions[0].organization_configured is True
    assert plan.suggestions[0].due_on == date(2026, 9, 9)


def test_production_adapter_has_no_historical_foreign_key_or_sqlite_only_upsert():
    source = Path(
        "infrastructure/persistence/teamworks_hr_lifecycle_template_repository.py"
    ).read_text(encoding="utf-8").lower()

    for forbidden in (
        "foreign key",
        "on conflict",
        "insert or replace",
        "insert or ignore",
        "pragma ",
        "import sqlite3",
    ):
        assert forbidden not in source
    for historical_table in ("personnes", "contrats"):
        assert f"from {historical_table}" not in source
        assert f"join {historical_table}" not in source
        assert f"update {historical_table}" not in source
        assert f"insert into {historical_table}" not in source


def test_runtime_facade_does_not_expose_structure_identity_or_repository():
    source = Path("application/bootstrap/hr_lifecycle_planning_factory.py").read_text(
        encoding="utf-8"
    )

    public_section = source.split("class HrLifecyclePlanningRuntimeFactory", 1)[0]
    assert "structure_ref: str" not in public_section.split("def plan", 1)[1].split(")", 1)[0]
    assert "repository" not in public_section.split("def plan", 1)[1].split(":", 1)[0]
