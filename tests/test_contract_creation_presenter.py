import unittest

from application.control.contract_creation_presenter import ContractCreationPresenter
from domain.contracts.contract_creation_rules import CEEQualification, ConventionCode
from domain.contracts.contract_type import ContractType


class ContractCreationPresenterTests(unittest.TestCase):
    def setUp(self):
        self.presenter = ContractCreationPresenter()

    def test_cee_uses_qualification_not_classification_or_point_value(self):
        state = self.presenter.build_state(
            convention=ConventionCode.CCNS,
            contract_type=ContractType.CEE,
        )

        self.assertTrue(state.show_cee_qualification)
        self.assertFalse(state.show_classification)
        self.assertFalse(state.show_point_value)
        self.assertEqual(state.classification_label, "Qualification / statut CEE :")
        self.assertIn(
            (CEEQualification.BAFA_HOLDER, "BAFA titulaire"),
            state.cee_qualification_choices,
        )
        self.assertIn(
            (CEEQualification.BAFA_TRAINEE, "BAFA stagiaire"),
            state.cee_qualification_choices,
        )

    def test_cee_preserves_legacy_classification_as_compatibility_warning(self):
        state = self.presenter.build_state(
            convention=ConventionCode.CCNS,
            contract_type=ContractType.CEE,
            legacy_classification_present=True,
        )
        self.assertIn("historique", state.warning)
        self.assertFalse(state.show_classification)

    def test_ccns_standard_contract_uses_ccns_classification(self):
        state = self.presenter.build_state(
            convention=ConventionCode.CCNS,
            contract_type=ContractType.CDD,
        )
        self.assertTrue(state.show_classification)
        self.assertTrue(state.classification_required)
        self.assertEqual(state.classification_family, "CCNS_GROUPS")
        self.assertEqual(state.classification_label, "Classification CCNS :")
        self.assertFalse(state.show_cee_qualification)
        self.assertFalse(state.show_point_value)

    def test_eclat_and_centres_sociaux_do_not_share_classification_family(self):
        eclat = self.presenter.build_state(
            convention=ConventionCode.ECLAT,
            contract_type=ContractType.CDI,
        )
        centres = self.presenter.build_state(
            convention=ConventionCode.CENTRES_SOCIAUX,
            contract_type=ContractType.CDI,
        )
        self.assertEqual(eclat.classification_family, "ECLAT_CLASSIFICATIONS")
        self.assertEqual(centres.classification_family, "CENTRES_SOCIAUX_CLASSIFICATIONS")
        self.assertNotEqual(eclat.classification_family, centres.classification_family)

    def test_internship_does_not_require_conventional_classification(self):
        state = self.presenter.build_state(
            convention=ConventionCode.CCNS,
            contract_type=ContractType.INTERNSHIP,
        )
        self.assertFalse(state.classification_required)


if __name__ == "__main__":
    unittest.main()
