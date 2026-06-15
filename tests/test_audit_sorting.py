from teamworks.CcnsCore.audit_sorting import compute_row_severity, sort_audit_rows_by_person_and_severity


def test_compute_row_severity():
    row = {"anomalies": ["CONTRAT_SANS_GRILLE"]}
    label, rank = compute_row_severity(row)
    assert label == "blocking"
    assert rank == 0


def test_sort_by_person_then_severity():
    rows = [
        {"nom_complet": "Alice Martin", "IDcontrat": 2, "anomalies": []},
        {"nom_complet": "Alice Martin", "IDcontrat": 1, "anomalies": ["MINIMUM_CCNS_NON_ATTEINT"]},
        {"nom_complet": "Bob Durant", "IDcontrat": 3, "anomalies": ["CONTRAT_SANS_GRILLE"]},
    ]
    sorted_rows = sort_audit_rows_by_person_and_severity(rows)
    assert sorted_rows[0]["IDcontrat"] == 1
    assert sorted_rows[1]["IDcontrat"] == 2
    assert sorted_rows[2]["IDcontrat"] == 3
