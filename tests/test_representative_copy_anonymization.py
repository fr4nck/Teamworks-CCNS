from datetime import date
from pathlib import Path

import pytest

from application.services.representative_copy_anonymization import (
    assert_safe_recipe_database_name,
    build_sequential_mapping,
    synthetic_birth_date,
    synthetic_identity,
)


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "anonymize_qt_vanilla_recipe_db.py"


def _age(value: date, reference: date) -> int:
    return reference.year - value.year - (
        (reference.month, reference.day) < (value.month, value.day)
    )


def test_recipe_database_name_must_be_explicitly_safe_and_confirmed():
    with pytest.raises(ValueError):
        assert_safe_recipe_database_name("teamworks_prod", "teamworks_prod")

    with pytest.raises(ValueError):
        assert_safe_recipe_database_name(
            "teamworks_qt_vanilla_recette",
            "teamworks_qt_vanilla_recett",
        )

    assert_safe_recipe_database_name(
        "teamworks_qt_vanilla_recette",
        "teamworks_qt_vanilla_recette",
    )


def test_synthetic_identity_is_deterministic_and_uses_reserved_contact_data():
    first = synthetic_identity(17)
    second = synthetic_identity(17)

    assert first == second
    assert first.email.endswith("@example.test")
    assert first.phone.startswith("00000")
    assert first.address
    assert first.city
    assert first.date_shift_days % 7 == 0
    assert first.date_shift_days != 0


def test_birth_date_replacement_preserves_minor_or_adult_group():
    reference = date(2026, 9, 21)

    minor = synthetic_birth_date(date(2012, 3, 4), 1, reference_date=reference)
    adult = synthetic_birth_date(date(1989, 7, 8), 2, reference_date=reference)

    assert minor is not None
    assert adult is not None
    assert _age(minor, reference) < 18
    assert _age(adult, reference) >= 18
    assert minor != date(2012, 3, 4)
    assert adult != date(1989, 7, 8)


def test_id_mapping_is_dense_and_does_not_reuse_the_original_values():
    mapping = build_sequential_mapping([7421, 12, 9914, 12], start=100001)

    assert mapping == {
        12: 100001,
        7421: 100002,
        9914: 100003,
    }
    assert set(mapping).isdisjoint(mapping.values())


def test_anonymizer_has_destructive_safety_gates_and_no_password_argument():
    source = TOOL.read_text(encoding="utf-8")

    assert '--database' in source
    assert '--confirm-database' in source
    assert '--apply' in source
    assert '--acknowledge-nontransactional' in source
    assert 'TEAMWORKS_MYSQL_PASSWORD' in source
    assert 'use_pure=True' in source
    assert '"--password"' not in source
    assert "'--password'" not in source

    assert '("photos", "documents")' in source
    assert 'FOREIGN_KEY_CHECKS=0' in source
    assert 'audit_anonymized_copy' in source
    assert 'connection.rollback()' in source
    assert 'connection.commit()' in source


def test_anonymizer_does_not_persist_the_reversible_id_mapping():
    source = TOOL.read_text(encoding="utf-8")

    assert "mapping_file" not in source
    assert "original_id" not in source
    assert '"persons": len(people)' in source
    assert '"candidates": len(candidates)' in source
    assert '"tw_people": len(tw_people)' in source
