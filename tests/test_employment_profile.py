from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from domain.contracts.employment_profile import EmploymentProfile
from domain.contracts.employment_regime import EmploymentRegime


def test_employment_regime_includes_required_regimes():
    assert {regime.name for regime in EmploymentRegime} >= {
        "CCNS_STANDARD",
        "CEE",
        "APPRENTICESHIP",
        "CIVIC_SERVICE",
        "INTERNSHIP",
        "VOLUNTEER",
        "EXTERNAL_PROVIDER",
    }


def test_employment_profile_exposes_its_business_requirements():
    profile_id = uuid4()
    profile = EmploymentProfile(
        id=profile_id,
        name="  Animateur CEE  ",
        regime=EmploymentRegime.CEE,
        subject_to_ccns=True,
        subject_to_salary_grid=False,
        subject_to_working_time_controls=False,
        subject_to_cee_controls=True,
    )

    assert profile.id == profile_id
    assert profile.name == "Animateur CEE"
    assert profile.is_ccns() is True
    assert profile.requires_salary_grid() is False
    assert profile.requires_working_time_controls() is False
    assert profile.requires_cee_controls() is True
    assert profile.active is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"id": "not-a-uuid"}, "UUID"),
        ({"name": " "}, "nom"),
        ({"regime": "CEE"}, "régime d'emploi"),
        ({"subject_to_ccns": 1}, "booléen"),
        ({"active": "yes"}, "booléen"),
    ],
)
def test_employment_profile_rejects_invalid_data(kwargs, message):
    profile_data = {
        "name": "Profil standard",
        "regime": EmploymentRegime.CCNS_STANDARD,
        "subject_to_ccns": True,
        "subject_to_salary_grid": True,
        "subject_to_working_time_controls": True,
        "subject_to_cee_controls": False,
    }
    profile_data.update(kwargs)

    with pytest.raises(ValueError, match=message):
        EmploymentProfile(**profile_data)


def test_employment_profile_is_immutable():
    profile = EmploymentProfile(
        name="Profil bénévole",
        regime=EmploymentRegime.VOLUNTEER,
        subject_to_ccns=False,
        subject_to_salary_grid=False,
        subject_to_working_time_controls=False,
        subject_to_cee_controls=False,
    )

    with pytest.raises(FrozenInstanceError):
        profile.active = False
