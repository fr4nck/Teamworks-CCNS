from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODERN_PAGE = ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_contrat_p3_modern.py"


def test_operation_choices_are_structured_and_visible_in_general_characteristics() -> None:
    source = MODERN_PAGE.read_text(encoding="utf-8")

    assert 'u"Nouveau contrat"' in source
    assert 'u"Renouvellement d\'un CDD"' in source
    assert 'u"Passage CDD → CDI"' in source
    assert 'u"Nature de l\'opération :"' in source
    assert 'u"Contrat précédent :"' in source


def test_legacy_trial_controls_cannot_reappear_after_rule_refresh() -> None:
    source = MODERN_PAGE.read_text(encoding="utf-8")

    assert "def _HideLegacyTrialControls(self):" in source
    assert '("label_essai", "periode_essai", "aide_essai")' in source
    assert "def RefreshContractRules(self):" in source
    assert "super().RefreshContractRules()" in source
    assert "self._HideLegacyTrialControls()" in source


def test_modern_trial_ui_exposes_optional_structured_duration() -> None:
    source = MODERN_PAGE.read_text(encoding="utf-8")

    assert 'u"Prévoir une période d\'essai"' in source
    assert 'u"jour(s) calendaires"' in source
    assert 'u"mois calendaires"' in source
    assert "trial_period_value" in source
    assert "trial_period_unit" in source
    assert "_ValidateTrialMaximum" in source


def test_g7_g8_use_annual_reference_salary_instead_of_fake_monthly_salary() -> None:
    source = MODERN_PAGE.read_text(encoding="utf-8")

    assert 'u"Rémunération annuelle de référence :"' in source
    assert 'u"€ brut / an"' in source
    assert "choice.periodicity is SalaryMinimumPeriodicity.ANNUAL" in source
    assert "gross_annual_salary" in source
