from domain.contracts.employment_regime import EmploymentRegime


def test_employment_regimes_are_unique_canonical_business_values():
    expected_members = {
        "CCNS_STANDARD",
        "CCNS_MODULATION",
        "CCNS_CDII",
        "APPRENTICE",
        "CEE",
        "PEC_CUI_CAE",
        "SERVICE_CIVIQUE",
        "STAGE_PFMP",
        "VOLUNTEER",
        "MANUAL_OUTSIDE_SCOPE",
    }

    assert set(EmploymentRegime.__members__) == expected_members
    assert len({regime.value for regime in EmploymentRegime}) == len(EmploymentRegime)
