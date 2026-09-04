from datetime import date

import pytest

from domain.hr_connections import (
    ConnectionProfile,
    ConnectorCapability,
    EffectivePeriod,
    HrOrganization,
    OrganizationKind,
    OrganizationReference,
    PortalLink,
)


def test_organization_kind_covers_initial_connector_families():
    assert {kind.value for kind in OrganizationKind} == {
        "urssaf",
        "net_entreprises",
        "mutuelle",
        "prevoyance",
        "retraite_complementaire",
        "opco",
        "spst",
        "france_travail",
        "other",
    }


def test_hr_organization_requires_stable_code_label_and_kind():
    organization = HrOrganization.create(
        code=" urssaf-bretagne ",
        label=" URSSAF Bretagne ",
        kind=OrganizationKind.URSSAF,
    )

    assert organization.code == "urssaf-bretagne"
    assert organization.label == "URSSAF Bretagne"

    with pytest.raises(ValueError):
        HrOrganization.create(code=" ", label="URSSAF", kind=OrganizationKind.URSSAF)
    with pytest.raises(ValueError):
        HrOrganization.create(code="urssaf", label=" ", kind=OrganizationKind.URSSAF)
    with pytest.raises(TypeError):
        HrOrganization.create(code="urssaf", label="URSSAF", kind="urssaf")  # type: ignore[arg-type]


def test_effective_period_rejects_inverted_dates_and_is_inclusive():
    period = EffectivePeriod(starts_on=date(2026, 1, 1), ends_on=date(2026, 12, 31))

    assert period.includes(date(2026, 1, 1))
    assert period.includes(date(2026, 12, 31))
    assert not period.includes(date(2025, 12, 31))
    assert not period.includes(date(2027, 1, 1))

    with pytest.raises(ValueError):
        EffectivePeriod(starts_on=date(2026, 2, 1), ends_on=date(2026, 1, 31))


def test_portal_link_accepts_http_urls_but_never_embedded_credentials():
    link = PortalLink.create(
        url=" https://www.net-entreprises.fr/ ",
        label=" Net-entreprises ",
    )

    assert link.url == "https://www.net-entreprises.fr/"
    assert link.label == "Net-entreprises"

    with pytest.raises(ValueError):
        PortalLink.create(url="ftp://example.org", label="FTP")
    with pytest.raises(ValueError):
        PortalLink.create(url="https://user:secret@example.org", label="Portail")


def test_organization_reference_is_non_secret_by_construction():
    reference = OrganizationReference.create(
        reference_type=" Numéro adhérent ",
        value=" 123456 ",
        label=" Contrat collectif ",
    )

    assert reference.reference_type == "numéro_adhérent"
    assert reference.value == "123456"
    assert reference.label == "Contrat collectif"

    for sensitive_type in ("password", "token", "api-key", "private key"):
        with pytest.raises(ValueError):
            OrganizationReference.create(reference_type=sensitive_type, value="secret")


def test_connection_profile_keeps_non_secret_data_immutable_and_queryable():
    organization = HrOrganization.create(
        code="mutuelle-reference",
        label="Mutuelle de référence",
        kind=OrganizationKind.MUTUELLE,
    )
    profile = ConnectionProfile.create(
        structure_ref=" structure-1 ",
        organization=organization,
        capabilities={ConnectorCapability.DEEP_LINK, ConnectorCapability.MANUAL_STATUS},
        references=[
            OrganizationReference.create(reference_type="contrat", value="COLLECTIF-1")
        ],
        portal_links=[
            PortalLink.create(url="https://example.org/espace-employeur", label="Espace employeur")
        ],
        effective_period=EffectivePeriod(starts_on=date(2026, 1, 1)),
    )

    assert profile.structure_ref == "structure-1"
    assert profile.supports(ConnectorCapability.DEEP_LINK)
    assert not profile.supports(ConnectorCapability.API)
    assert profile.references[0].value == "COLLECTIF-1"
    assert profile.portal_links[0].label == "Espace employeur"
