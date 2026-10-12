import sqlite3
from pathlib import Path

import pytest

from application.bootstrap.hr_lifecycle_template_management_factory import (
    HrLifecycleTemplateManagementRuntimeFactory,
)
from application.services.hr_connections.hr_lifecycle_template_management import (
    HrLifecycleTemplateManagementService,
    HrLifecycleTemplateRequest,
)
from domain.hr_connections import (
    ConnectionProfile,
    ExpectedDocument,
    HrLifecycleEventKind,
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


class FakeTemplateRepository:
    def __init__(self):
        self.items = {}
        self.saved = []

    def get_template(self, *, structure_ref, template_id):
        return self.items.get((structure_ref, template_id))

    def list_all_templates(self, *, structure_ref):
        return tuple(
            item
            for (item_structure_ref, _), item in self.items.items()
            if item_structure_ref == structure_ref
        )

    def save_template(self, *, structure_ref, template):
        self.items[(structure_ref, template.template_id)] = template
        self.saved.append(template)
        return template


class FakeProfiles:
    def __init__(self, configured=()):
        self.configured = set(configured)

    def get_profile(self, *, structure_ref, organization_code):
        if organization_code in self.configured:
            return object()
        return None


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


def _request(template_id="modele-1", *, enabled=True):
    return HrLifecycleTemplateRequest(
        template_id=template_id,
        event_kind=HrLifecycleEventKind.EMPLOYMENT_START,
        organization_code="urssaf",
        case_type_code="demarche-locale",
        case_type_label="Démarche locale",
        due_offset_days=2,
        expected_documents=(
            ExpectedDocument.create(
                code="piece-locale",
                label="Pièce locale",
                required=True,
            ),
        ),
        enabled=enabled,
    )


def test_save_uses_only_explicit_request_and_requires_configured_organization():
    repository = FakeTemplateRepository()
    service = HrLifecycleTemplateManagementService(
        repository=repository,
        profile_repository=FakeProfiles(("urssaf",)),
    )

    template = service.save(structure_ref="structure-a", request=_request())

    assert template.template_id == "modele-1"
    assert template.event_kind is HrLifecycleEventKind.EMPLOYMENT_START
    assert template.organization_code == "urssaf"
    assert template.case_type.code == "demarche-locale"
    assert template.due_offset_days == 2
    assert [item.code for item in template.expected_documents] == ["piece-locale"]
    assert repository.saved == [template]


def test_save_rejects_unconfigured_organization_without_persisting():
    repository = FakeTemplateRepository()
    service = HrLifecycleTemplateManagementService(
        repository=repository,
        profile_repository=FakeProfiles(),
    )

    with pytest.raises(LookupError, match="doit être configuré"):
        service.save(structure_ref="structure-a", request=_request())

    assert repository.saved == []


def test_disable_preserves_configuration_and_never_deletes_template():
    repository = FakeTemplateRepository()
    service = HrLifecycleTemplateManagementService(
        repository=repository,
        profile_repository=FakeProfiles(("urssaf",)),
    )
    current = service.save(structure_ref="structure-a", request=_request())
    repository.saved.clear()

    disabled = service.disable(structure_ref="structure-a", template_id=current.template_id)

    assert disabled.enabled is False
    assert disabled.event_kind is current.event_kind
    assert disabled.organization_code == current.organization_code
    assert disabled.case_type == current.case_type
    assert disabled.due_offset_days == current.due_offset_days
    assert disabled.expected_documents == current.expected_documents
    assert repository.saved == [disabled]
    assert not hasattr(repository, "delete_template")


def test_disable_is_idempotent_for_already_disabled_template():
    repository = FakeTemplateRepository()
    service = HrLifecycleTemplateManagementService(
        repository=repository,
        profile_repository=FakeProfiles(("urssaf",)),
    )
    disabled = service.save(
        structure_ref="structure-a",
        request=_request(enabled=False),
    )
    repository.saved.clear()

    assert service.disable(
        structure_ref="structure-a",
        template_id=disabled.template_id,
    ) is disabled
    assert repository.saved == []


def test_list_all_templates_reads_all_event_kinds_with_documents(tmp_path):
    path = tmp_path / "lifecycle-management.sqlite"
    repository = TeamworksHrLifecycleTemplateRepository(db_factory=_factory(path))
    profiles = TeamworksHrConnectionsRepository(db_factory=_factory(path))
    identity = TeamworksStructureIdentityRepository(db_factory=_factory(path))
    structure_ref = identity.get_or_create_structure_ref()
    profiles.save_profile(
        ConnectionProfile.create(
            structure_ref=structure_ref,
            organization=HrOrganization.create(
                code="urssaf",
                label="Organisme A",
                kind=OrganizationKind.URSSAF,
            ),
        )
    )
    runtime = HrLifecycleTemplateManagementRuntimeFactory(
        db_factory=_factory(path),
    ).create()
    runtime.save(_request("start"))
    runtime.save(
        HrLifecycleTemplateRequest(
            template_id="end",
            event_kind=HrLifecycleEventKind.EMPLOYMENT_END,
            organization_code="urssaf",
            case_type_code="sortie",
            case_type_label="Sortie locale",
        )
    )

    listed = runtime.list_templates()
    organizations = runtime.list_organizations()

    assert {item.template_id for item in listed} == {"start", "end"}
    assert {item.event_kind for item in listed} == {
        HrLifecycleEventKind.EMPLOYMENT_START,
        HrLifecycleEventKind.EMPLOYMENT_END,
    }
    assert next(item for item in listed if item.template_id == "start").expected_documents
    assert [(item.code, item.label) for item in organizations] == [("urssaf", "Organisme A")]
    assert repository.list_all_templates(structure_ref=structure_ref) == listed


def test_management_layer_has_no_regulatory_catalog_network_or_delete_api():
    service_source = Path(
        "application/services/hr_connections/hr_lifecycle_template_management.py"
    ).read_text(encoding="utf-8").lower()
    runtime_source = Path(
        "application/bootstrap/hr_lifecycle_template_management_factory.py"
    ).read_text(encoding="utf-8").lower()
    repository_source = Path(
        "infrastructure/persistence/teamworks_hr_lifecycle_template_repository.py"
    ).read_text(encoding="utf-8").lower()

    assert "delete_template" not in service_source
    assert "delete_template" not in runtime_source
    assert "delete_template" not in repository_source
    for forbidden in (
        "requests.",
        "urllib",
        "webbrowser",
        "selenium",
        "playwright",
        "dpae",
        "net-entreprises",
    ):
        assert forbidden not in service_source
        assert forbidden not in runtime_source
    public_runtime = runtime_source.split(
        "class hrlifecycletemplatemanagementruntimefactory", 1
    )[0]
    assert "gestiondb" not in public_runtime
