import inspect

import application.services.hr_connections.reference_connectors as reference_connectors


def test_reference_connector_catalog_does_not_hardcode_external_urls():
    source = inspect.getsource(reference_connectors)

    assert "http://" not in source
    assert "https://" not in source


def test_reference_connector_catalog_does_not_claim_automated_transport():
    source = inspect.getsource(reference_connectors)

    for forbidden in ("ConnectorCapability.API", "ConnectorCapability.SUBMISSION", "STATUS_SYNC"):
        assert forbidden not in source
