from teamworks.CcnsCore.audit_filters import filter_audit_rows


def test_filter_anomalies_only():
    rows = [
        {"IDcontrat": 1, "classification": "G3", "type_contrat": "CDI", "salaire_base": 1800, "anomalies": ["A1"]},
        {"IDcontrat": 2, "classification": "G4", "type_contrat": "CDD", "salaire_base": 2200, "anomalies": []},
    ]
    filtered = filter_audit_rows(rows, anomalies_only=True)
    assert len(filtered) == 1
    assert filtered[0]["IDcontrat"] == 1


def test_filter_by_group_and_type():
    rows = [
        {"IDcontrat": 1, "classification": "G3", "type_contrat": "CDI", "salaire_base": 1800, "anomalies": ["A1"]},
        {"IDcontrat": 2, "classification": "G4", "type_contrat": "CDD", "salaire_base": 2200, "anomalies": []},
    ]
    filtered = filter_audit_rows(rows, classification_filter="G4", contract_type_filter="CDD")
    assert len(filtered) == 1
    assert filtered[0]["IDcontrat"] == 2
