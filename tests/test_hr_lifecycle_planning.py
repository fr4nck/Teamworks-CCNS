from datetime import date
from pathlib import Path

import pytest

from application.services.hr_connections import HrLifecyclePlanningService
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


class FakeTemplateRepository:
    def __init__(self, templates=()):
        self.templates = tuple(templates)
        self.calls = []

    def list_templates(self, *, structure_ref, event_kind):
        self.calls.append((structure_ref, event_kind))
        return self.templates


class FakeProfileRepository:
    def __init__(self, profiles=()):
        self.profiles = tuple(profiles)
        self.calls = []

    def list_profiles(self, *, structure_ref):
        self.calls.append(structure_ref)
        return self.profiles

    def get_profile(self, *, structure_ref, organization_code):
        raise AssertionError("La projection doit charger les organismes en groupe.")

    def save_profile(self, profile):
        raise AssertionError("La planification du cycle de vie est en lecture seule.")


def _event(kind=HrLifecycleEventKind.EMPLOYMENT_START):
    return HrLifecycleEvent.create(
        event_id="event-42-start",
        kind=kind,
        person_ref="42",
        effective_on=date(2026, 9, 7),
        source_ref="contract-99",
    )


def _template(
    template_id="template-1",
    *,
    kind=HrLifecycleEventKind.EMPLOYMENT_START,
    organization_code="urssaf",
    due_offset_days=None,
    enabled=True,
):
    return HrLifecycleTemplate.create(
        template_id=template_id,
        event_kind=kind,
        organization_code=organization_code,
        case_type=HrCaseType.create(code="local-start", label="Démarche locale d'embauche"),
        due_offset_days=due_offset_days,
        expected_documents=(
            ExpectedDocument.create(
                code="piece-locale",
                label="Pièce définie par la structure",
                required=True,
            ),
        ),
        enabled=enabled,
    )


def _profile(code="urssaf"):
    return ConnectionProfile.create(
        structure_ref="structure-1",
        organization=HrOrganization.create(
            code=code,
            label="Organisme configuré",
            kind=OrganizationKind.URSSAF,
        ),
    )


def _service(templates=(), profiles=()):
    template_repository = FakeTemplateRepository(templates)
    profile_repository = FakeProfileRepository(profiles)
    return (
        HrLifecyclePlanningService(
            template_repository=template_repository,
            profile_repository=profile_repository,
        ),
        template_repository,
        profile_repository,
    )


def test_lifecycle_domain_validates_event_and_explicit_template():
    event = _event()
    template = _template(due_offset_days=3)

    assert event.person_ref == "42"
    assert event.kind is HrLifecycleEventKind.EMPLOYMENT_START
    assert template.organization_code == "urssaf"
    assert template.due_offset_days == 3
    assert template.expected_documents[0].required is True

    with pytest.raises(ValueError):
        HrLifecycleEvent.create(
            event_id=" ",
            kind=HrLifecycleEventKind.EMPLOYMENT_START,
            person_ref="42",
            effective_on=date(2026, 9, 7),
        )
    with pytest.raises(TypeError):
        HrLifecycleTemplate.create(
            template_id="template",
            event_kind=HrLifecycleEventKind.EMPLOYMENT_START,
            organization_code="urssaf",
            case_type=HrCaseType.create(code="x", label="X"),
            due_offset_days=True,
        )


def test_lifecycle_plan_is_empty_without_explicit_templates():
    service, templates, profiles = _service(profiles=(_profile(),))

    plan = service.plan(structure_ref="structure-1", event=_event())

    assert plan.suggestions == ()
    assert plan.suggestion_count == 0
    assert plan.unconfigured_organization_count == 0
    assert templates.calls == [
        ("structure-1", HrLifecycleEventKind.EMPLOYMENT_START)
    ]
    assert profiles.calls == ["structure-1"]


def test_enabled_template_builds_deterministic_suggestion_from_explicit_configuration():
    service, _, _ = _service(
        templates=(_template(due_offset_days=5),),
        profiles=(_profile(),),
    )

    first = service.plan(structure_ref="structure-1", event=_event()).suggestions[0]
    second = service.plan(structure_ref="structure-1", event=_event()).suggestions[0]

    assert first.suggestion_key == second.suggestion_key
    assert len(first.suggestion_key) == 64
    assert first.person_ref == "42"
    assert first.organization_code == "urssaf"
    assert first.organization_configured is True
    assert first.opened_on == date(2026, 9, 7)
    assert first.due_on == date(2026, 9, 12)
    assert first.expected_documents[0].code == "piece-locale"
    assert first.source_ref == "contract-99"


def test_template_without_due_offset_does_not_invent_deadline():
    service, _, _ = _service(
        templates=(_template(due_offset_days=None),),
        profiles=(_profile(),),
    )

    suggestion = service.plan(
        structure_ref="structure-1",
        event=_event(),
    ).suggestions[0]

    assert suggestion.due_on is None


def test_disabled_template_is_ignored_and_does_not_create_placeholder():
    service, _, _ = _service(
        templates=(
            _template(template_id="disabled", enabled=False),
            _template(template_id="enabled"),
        ),
        profiles=(_profile(),),
    )

    plan = service.plan(structure_ref="structure-1", event=_event())

    assert [item.template_id for item in plan.suggestions] == ["enabled"]


def test_missing_organization_remains_descriptive_instead_of_blocking_or_creating_it():
    service, _, profiles = _service(
        templates=(_template(organization_code="unconfigured"),),
        profiles=(_profile(),),
    )

    plan = service.plan(structure_ref="structure-1", event=_event())

    assert plan.suggestion_count == 1
    assert plan.unconfigured_organization_count == 1
    assert plan.suggestions[0].organization_configured is False
    assert profiles.calls == ["structure-1"]


def test_repository_cannot_mix_event_kinds_or_duplicate_active_template_ids():
    foreign_service, _, _ = _service(
        templates=(
            _template(kind=HrLifecycleEventKind.EMPLOYMENT_END),
        ),
    )
    with pytest.raises(ValueError, match="étranger"):
        foreign_service.plan(structure_ref="structure-1", event=_event())

    duplicate_service, _, _ = _service(
        templates=(
            _template(template_id="same"),
            _template(template_id="same", organization_code="other"),
        ),
    )
    with pytest.raises(ValueError, match="même identifiant"):
        duplicate_service.plan(structure_ref="structure-1", event=_event())


def test_template_refuses_duplicate_expected_document_codes():
    case_type = HrCaseType.create(code="local", label="Local")
    duplicate_documents = (
        ExpectedDocument.create(code="same", label="A", required=True),
        ExpectedDocument.create(code="same", label="B", required=False),
    )

    with pytest.raises(ValueError, match="même pièce"):
        HrLifecycleTemplate.create(
            template_id="template",
            event_kind=HrLifecycleEventKind.CONTRACT_CHANGED,
            organization_code="org",
            case_type=case_type,
            expected_documents=duplicate_documents,
        )


def test_lifecycle_planning_has_no_persistence_ui_or_external_transport():
    source = Path(
        "application/services/hr_connections/hr_lifecycle_planning.py"
    ).read_text(encoding="utf-8").lower()

    for token in (
        "import wx",
        "gestiondb",
        "sqlite3",
        "requests",
        "webbrowser",
        "hrcasecreationservice",
        "save_case(",
        "persist_",
        "append_event",
    ):
        assert token not in source
