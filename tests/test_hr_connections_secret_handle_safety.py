import pytest

from domain.hr_connections import SecretHandle, SecretKind


@pytest.mark.parametrize(
    "store_key",
    [
        "teamworks/hr/connector/my secret",
        "teamworks/hr/connector/my\tsecret",
        "teamworks/hr/connector/my\nsecret",
        "teamworks/hr/connector/my\rsecret",
    ],
)
def test_secret_handle_rejects_whitespace_in_opaque_store_key(store_key):
    with pytest.raises(ValueError):
        SecretHandle.create(store_key=store_key, kind=SecretKind.PASSWORD)


def test_secret_handle_accepts_structured_non_secret_identifier():
    handle = SecretHandle.create(
        store_key="teamworks/hr/net-entreprises/client-certificate.v1",
        kind=SecretKind.CERTIFICATE,
    )

    assert handle.store_key == "teamworks/hr/net-entreprises/client-certificate.v1"
