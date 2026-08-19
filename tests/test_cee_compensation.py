from datetime import date
from decimal import Decimal
import unittest

from domain.contracts.cee_compensation import legal_cee_daily_minimum
from domain.convention.smic import SmicTerritory, create_smic_catalog_2026


class CEECompensationTests(unittest.TestCase):
    def test_metropolitan_minimum_from_june_2026_smic(self):
        minimum = legal_cee_daily_minimum(
            smic_catalog=create_smic_catalog_2026(),
            reference_date=date(2026, 8, 19),
            territory=SmicTerritory.METROPOLITAN_FRANCE,
        )
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


if __name__ == "__main__":
    unittest.main()
