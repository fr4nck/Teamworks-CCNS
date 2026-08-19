from datetime import date
from decimal import Decimal, localcontext
import unittest

from domain.contracts.cee_compensation import (
    legal_cee_daily_minimum,
    legal_cee_daily_smic_multiplier_on,
)
from domain.convention.smic import (
    SmicCatalog,
    SmicTerritory,
    SmicVersion,
    create_smic_catalog_2026,
)


class CEECompensationTests(unittest.TestCase):
    def test_metropolitan_minimum_from_june_2026_smic(self):
        minimum = legal_cee_daily_minimum(
            smic_catalog=create_smic_catalog_2026(),
            reference_date=date(2026, 8, 19),
            territory=SmicTerritory.METROPOLITAN_FRANCE,
        )
        self.assertEqual(minimum, Decimal("52.93"))

    def test_minimum_is_independent_from_ambient_decimal_precision(self):
        # Régression observée dans le portable : avec prec=2, la multiplication
        # 12,31 × 4,30 était arrondie à 53 AVANT le quantize, d'où 53,00 €.
        with localcontext() as context:
            context.prec = 2
            minimum = legal_cee_daily_minimum(
                smic_catalog=create_smic_catalog_2026(),
                reference_date=date(2026, 8, 19),
            )
            self.assertEqual(context.prec, 2)
        self.assertEqual(minimum, Decimal("52.93"))

    def test_uses_smic_version_applicable_on_contract_date(self):
        catalog = create_smic_catalog_2026()
        january = legal_cee_daily_minimum(
            smic_catalog=catalog,
            reference_date=date(2026, 2, 1),
        )
        june = legal_cee_daily_minimum(
            smic_catalog=catalog,
            reference_date=date(2026, 6, 1),
        )
        self.assertEqual(january, Decimal("51.69"))
        self.assertEqual(june, Decimal("52.93"))
        self.assertLess(january, june)

    def test_legal_multiplier_changes_on_may_1_2025(self):
        self.assertEqual(
            legal_cee_daily_smic_multiplier_on(date(2025, 4, 30)),
            Decimal("2.20"),
        )
        self.assertEqual(
            legal_cee_daily_smic_multiplier_on(date(2025, 5, 1)),
            Decimal("4.30"),
        )

    def test_daily_minimum_uses_historical_multiplier(self):
        catalog = SmicCatalog(
            (
                SmicVersion(
                    code="SMIC-TEST-2025",
                    name="SMIC test 2025",
                    territory=SmicTerritory.METROPOLITAN_FRANCE,
                    effective_from=date(2025, 4, 1),
                    effective_until=date(2025, 5, 31),
                    hourly_gross_amount=Decimal("10.00"),
                    monthly_gross_amount_35h=Decimal("1516.70"),
                    legal_weekly_hours=Decimal("35.00"),
                    source_reference="Valeur de test pour vérifier la règle CEE datée",
                ),
            )
        )
        self.assertEqual(
            legal_cee_daily_minimum(
                smic_catalog=catalog,
                reference_date=date(2025, 4, 30),
            ),
            Decimal("22.00"),
        )
        self.assertEqual(
            legal_cee_daily_minimum(
                smic_catalog=catalog,
                reference_date=date(2025, 5, 1),
            ),
            Decimal("43.00"),
        )

    def test_no_rule_is_invented_before_supported_history(self):
        with self.assertRaises(ValueError):
            legal_cee_daily_smic_multiplier_on(date(2008, 4, 30))


if __name__ == "__main__":
    unittest.main()
