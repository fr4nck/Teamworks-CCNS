from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.convention import (
    SmicCatalog,
    SmicTerritory,
    SmicVersion,
    create_mayotte_smic_2026_01,
    create_mayotte_smic_2026_06,
    create_metropolitan_smic_2026_01,
    create_metropolitan_smic_2026_06,
    create_smic_catalog_2026,
)


def smic(
    code: str = "SMIC-A",
    territory: SmicTerritory = SmicTerritory.METROPOLITAN_FRANCE,
    start: date = date(2026, 1, 1),
    end: date | None = date(2026, 5, 31),
    hourly: Decimal = Decimal("12.024"),
    monthly: Decimal = Decimal("1823.034"),
    weekly: Decimal = Decimal("35.00"),
    active: bool = True,
    id: UUID | None = None,
) -> SmicVersion:
    kwargs = {
        "code": code,
        "name": " SMIC test ",
        "territory": territory,
        "effective_from": start,
        "effective_until": end,
        "hourly_gross_amount": hourly,
        "monthly_gross_amount_35h": monthly,
        "legal_weekly_hours": weekly,
        "source_reference": " Source officielle ",
        "active": active,
    }
    if id is not None:
        kwargs["id"] = id
    return SmicVersion(**kwargs)


def test_smic_version_creations_valides_metropole_et_mayotte():
    metropolitan = smic()
    mayotte = smic("SMIC-M", SmicTerritory.MAYOTTE)
    assert metropolitan.is_metropolitan() and not metropolitan.is_mayotte()
    assert mayotte.is_mayotte() and not mayotte.is_metropolitan()
    assert metropolitan.is_active()
    assert type(metropolitan.id) is UUID


def test_smic_version_normalise_code_nom_source_et_quantifie_montants():
    item = smic(" smic-test ")
    assert item.code == "SMIC-TEST"
    assert item.name == "SMIC test"
    assert item.source_reference == "Source officielle"
    assert item.hourly_gross_amount == Decimal("12.02")
    assert item.monthly_gross_amount_35h == Decimal("1823.03")
    assert item.legal_weekly_hours == Decimal("35.00")


@pytest.mark.parametrize("field", ["effective_from", "effective_until"])
def test_smic_version_refuse_datetime_pour_les_dates(field):
    kwargs = {"start": date(2026, 1, 1), "end": date(2026, 5, 31)}
    kwargs["start" if field == "effective_from" else "end"] = datetime(2026, 1, 1)
    with pytest.raises(TypeError):
        smic(**kwargs)


def test_smic_version_refuse_periode_inversee_et_accepte_periode_ouverte():
    with pytest.raises(ValueError):
        smic(start=date(2026, 6, 1), end=date(2026, 5, 31))
    assert smic(end=None).is_open_ended()


@pytest.mark.parametrize("bad", [1, 1.0, "1.00", True])
@pytest.mark.parametrize("field", ["hourly", "monthly", "weekly"])
def test_smic_version_exige_decimal_strict_pour_montants_et_duree(field, bad):
    kwargs = {field: bad}
    with pytest.raises(TypeError):
        smic(**kwargs)


@pytest.mark.parametrize("field", ["hourly", "monthly", "weekly"])
@pytest.mark.parametrize("bad", [Decimal("0"), Decimal("-1")])
def test_smic_version_refuse_montants_et_duree_non_positifs(field, bad):
    with pytest.raises(ValueError):
        smic(**{field: bad})


def test_smic_version_valide_territoire_source_active_uuid_et_immutabilite():
    explicit_id = uuid4()
    assert smic(id=explicit_id).id == explicit_id
    with pytest.raises(TypeError):
        smic(territory="metropolitan_france")
    with pytest.raises(ValueError):
        SmicVersion("A", "A", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, Decimal("1"), Decimal("1"), Decimal("35"), " ")
    with pytest.raises(TypeError):
        smic(active=1)
    with pytest.raises(TypeError):
        smic(id=str(explicit_id))
    with pytest.raises(FrozenInstanceError):
        smic().code = "B"


def test_smic_version_applies_on_aux_bornes_et_hors_periode():
    item = smic(start=date(2026, 1, 1), end=date(2026, 5, 31))
    assert item.applies_on(date(2026, 1, 1))
    assert item.applies_on(date(2026, 5, 31))
    assert not item.applies_on(date(2025, 12, 31))
    assert not item.applies_on(date(2026, 6, 1))
    with pytest.raises(TypeError):
        item.applies_on(datetime(2026, 1, 1))


def test_smic_catalog_valide_refuse_collections_invalides_doublons_et_conserve_ordre():
    first = smic("A", start=date(2026, 1, 1), end=date(2026, 5, 31))
    second = smic("B", start=date(2026, 6, 1), end=None)
    catalog = SmicCatalog((first, second))
    assert catalog.version_count() == 2
    assert catalog.versions == (first, second)
    with pytest.raises(TypeError):
        SmicCatalog([first])
    with pytest.raises(ValueError):
        SmicCatalog(())
    with pytest.raises(TypeError):
        SmicCatalog((first, "invalid"))
    with pytest.raises(ValueError, match="UUID"):
        SmicCatalog((first, smic("C", start=date(2027, 1, 1), end=None, id=first.id)))
    with pytest.raises(ValueError, match="codes"):
        SmicCatalog((first, smic("A", start=date(2027, 1, 1), end=None)))
    with pytest.raises(FrozenInstanceError):
        catalog.versions = ()


def test_smic_catalog_controle_chevauchements_par_territoire_et_autorise_trous():
    metro = smic("M1", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), date(2026, 12, 31))
    mayotte = smic("Y1", SmicTerritory.MAYOTTE, date(2026, 1, 1), date(2026, 12, 31))
    assert SmicCatalog((metro, mayotte)).version_count() == 2
    with pytest.raises(ValueError, match="chevaucher"):
        SmicCatalog((metro, smic("M2", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 6, 1), None)))
    with pytest.raises(ValueError, match="chevaucher"):
        SmicCatalog((mayotte, smic("Y2", SmicTerritory.MAYOTTE, date(2026, 6, 1), None)))
    gap = SmicCatalog((smic("G1", start=date(2026, 1, 1), end=date(2026, 1, 31)), smic("G2", start=date(2026, 3, 1), end=None)))
    assert not gap.has_version_for(date(2026, 2, 15), SmicTerritory.METROPOLITAN_FRANCE)


def test_smic_catalog_selection_par_date_et_territoire():
    catalog = create_smic_catalog_2026()
    assert catalog.version_applicable_on(date(2026, 5, 31), SmicTerritory.METROPOLITAN_FRANCE).code == "SMIC-METROPOLE-2026-01"
    assert catalog.version_applicable_on(date(2026, 6, 1), SmicTerritory.METROPOLITAN_FRANCE).code == "SMIC-METROPOLE-2026-06"
    assert catalog.hourly_amount_on(date(2026, 6, 1), SmicTerritory.MAYOTTE) == Decimal("9.56")
    assert catalog.monthly_amount_35h_on(date(2026, 1, 1), SmicTerritory.MAYOTTE) == Decimal("1415.05")
    assert catalog.has_version_for(date(2026, 1, 1), SmicTerritory.MAYOTTE)
    with pytest.raises(ValueError, match="Aucune version du SMIC"):
        catalog.version_applicable_on(date(2025, 12, 31), SmicTerritory.METROPOLITAN_FRANCE)
    with pytest.raises(TypeError):
        catalog.version_applicable_on(datetime(2026, 1, 1), SmicTerritory.METROPOLITAN_FRANCE)
    with pytest.raises(TypeError):
        catalog.version_applicable_on(date(2026, 1, 1), "mayotte")


def test_donnees_2026_exactes_et_nouvelles_instances():
    versions = (
        create_metropolitan_smic_2026_01(),
        create_mayotte_smic_2026_01(),
        create_metropolitan_smic_2026_06(),
        create_mayotte_smic_2026_06(),
    )
    assert [v.code for v in versions] == [
        "SMIC-METROPOLE-2026-01", "SMIC-MAYOTTE-2026-01", "SMIC-METROPOLE-2026-06", "SMIC-MAYOTTE-2026-06"
    ]
    assert [v.hourly_gross_amount for v in versions] == [Decimal("12.02"), Decimal("9.33"), Decimal("12.31"), Decimal("9.56")]
    assert [v.monthly_gross_amount_35h for v in versions] == [Decimal("1823.03"), Decimal("1415.05"), Decimal("1867.02"), Decimal("1449.93")]
    assert [v.effective_from for v in versions] == [date(2026, 1, 1), date(2026, 1, 1), date(2026, 6, 1), date(2026, 6, 1)]
    assert versions[0].effective_until == versions[1].effective_until == date(2026, 5, 31)
    assert versions[2].is_open_ended() and versions[3].is_open_ended()
    assert [v.territory for v in versions] == [SmicTerritory.METROPOLITAN_FRANCE, SmicTerritory.MAYOTTE, SmicTerritory.METROPOLITAN_FRANCE, SmicTerritory.MAYOTTE]
    assert all(v.source_reference for v in versions)
    assert all(type(v.hourly_gross_amount) is Decimal and type(v.monthly_gross_amount_35h) is Decimal for v in versions)
    assert create_metropolitan_smic_2026_01().id != create_metropolitan_smic_2026_01().id
    assert create_smic_catalog_2026().version_count() == 4
