import pytest

from domain.hr_connections import (
    ConnectorCredentialProfile,
    CredentialBinding,
    CredentialRequirement,
    SecretHandle,
    SecretKind,
    unavailable_secret_handles,
)


def _requirements():
    return (
        CredentialRequirement.create(
            code="username_password",
            label="Mot de passe du compte",
            kind=SecretKind.PASSWORD,
        ),
        CredentialRequirement.create(
            code="client_certificate",
            label="Certificat client",
            kind=SecretKind.CERTIFICATE,
            required=False,
        ),
    )


def test_secret_handle_is_opaque_and_contains_no_value_field():
    handle = SecretHandle.create(
        store_key="teamworks/hr/urssaf/password",
        kind=SecretKind.PASSWORD,
    )

    assert handle.store_key == "teamworks/hr/urssaf/password"
    assert handle.kind is SecretKind.PASSWORD
    assert not hasattr(handle, "value")
    assert not hasattr(handle, "secret")
    assert not hasattr(handle, "password")


def test_secret_handle_rejects_empty_whitespace_and_untyped_kind():
    with pytest.raises(ValueError):
        SecretHandle.create(store_key=" ", kind=SecretKind.PASSWORD)
    with pytest.raises(ValueError):
        SecretHandle.create(store_key="teamworks secret", kind=SecretKind.PASSWORD)
    with pytest.raises(TypeError):
        SecretHandle(store_key="teamworks/secret", kind="password")  # type: ignore[arg-type]


def test_credential_requirement_requires_typed_kind_and_boolean_required():
    with pytest.raises(ValueError):
        CredentialRequirement.create(
            code=" ",
            label="Mot de passe",
            kind=SecretKind.PASSWORD,
        )
    with pytest.raises(TypeError):
        CredentialRequirement(
            code="password",
            label="Mot de passe",
            kind=SecretKind.PASSWORD,
            required=1,  # type: ignore[arg-type]
        )


def test_profile_reports_missing_required_bindings_without_accessing_secret_values():
    profile = ConnectorCredentialProfile.create(
        connector_id="urssaf-api",
        requirements=_requirements(),
    )

    assert profile.missing_required_codes == frozenset({"username_password"})
    assert not profile.is_bound


def test_profile_accepts_matching_handle_and_leaves_optional_requirement_unbound():
    handle = SecretHandle.create(
        store_key="teamworks/hr/urssaf/password",
        kind=SecretKind.PASSWORD,
    )
    profile = ConnectorCredentialProfile.create(
        connector_id="urssaf-api",
        requirements=_requirements(),
        bindings=[
            CredentialBinding.create(
                requirement_code="username_password",
                secret_handle=handle,
            )
        ],
    )

    assert profile.is_bound
    assert profile.missing_required_codes == frozenset()
    assert profile.bound_requirement_codes == frozenset({"username_password"})


def test_profile_rejects_unknown_duplicate_or_wrong_kind_bindings():
    requirements = _requirements()
    password_handle = SecretHandle.create(
        store_key="teamworks/hr/urssaf/password",
        kind=SecretKind.PASSWORD,
    )
    token_handle = SecretHandle.create(
        store_key="teamworks/hr/urssaf/token",
        kind=SecretKind.ACCESS_TOKEN,
    )

    with pytest.raises(ValueError):
        ConnectorCredentialProfile.create(
            connector_id="urssaf-api",
            requirements=requirements,
            bindings=[
                CredentialBinding.create(
                    requirement_code="unknown",
                    secret_handle=password_handle,
                )
            ],
        )
    with pytest.raises(ValueError):
        ConnectorCredentialProfile.create(
            connector_id="urssaf-api",
            requirements=requirements,
            bindings=[
                CredentialBinding.create(
                    requirement_code="username_password",
                    secret_handle=password_handle,
                ),
                CredentialBinding.create(
                    requirement_code="username_password",
                    secret_handle=password_handle,
                ),
            ],
        )
    with pytest.raises(ValueError):
        ConnectorCredentialProfile.create(
            connector_id="urssaf-api",
            requirements=requirements,
            bindings=[
                CredentialBinding.create(
                    requirement_code="username_password",
                    secret_handle=token_handle,
                )
            ],
        )


def test_profile_rejects_duplicate_requirement_codes():
    first = CredentialRequirement.create(
        code="password",
        label="Mot de passe",
        kind=SecretKind.PASSWORD,
    )
    second = CredentialRequirement.create(
        code="password",
        label="Autre libellé",
        kind=SecretKind.PASSWORD,
    )

    with pytest.raises(ValueError):
        ConnectorCredentialProfile.create(
            connector_id="connector",
            requirements=[first, second],
        )


def test_secret_store_contract_checks_availability_without_read_method():
    available_handle = SecretHandle.create(
        store_key="teamworks/hr/connector/password",
        kind=SecretKind.PASSWORD,
    )
    missing_handle = SecretHandle.create(
        store_key="teamworks/hr/connector/certificate",
        kind=SecretKind.CERTIFICATE,
    )
    profile = ConnectorCredentialProfile.create(
        connector_id="connector",
        requirements=[
            CredentialRequirement.create(
                code="password",
                label="Mot de passe",
                kind=SecretKind.PASSWORD,
            ),
            CredentialRequirement.create(
                code="certificate",
                label="Certificat",
                kind=SecretKind.CERTIFICATE,
            ),
        ],
        bindings=[
            CredentialBinding.create(
                requirement_code="password",
                secret_handle=available_handle,
            ),
            CredentialBinding.create(
                requirement_code="certificate",
                secret_handle=missing_handle,
            ),
        ],
    )

    class FakeSecretStore:
        def __init__(self):
            self.checked = []

        def is_available(self, handle):
            self.checked.append(handle)
            return handle == available_handle

    store = FakeSecretStore()
    missing = unavailable_secret_handles(profile, store)

    assert missing == (missing_handle,)
    assert store.checked == [available_handle, missing_handle]
    assert not hasattr(store, "read")
    assert not hasattr(store, "get")
    assert not hasattr(store, "reveal")
