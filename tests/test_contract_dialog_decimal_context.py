from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Creation_contrat.py"
PAGE3 = ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_contrat_p3.py"


def test_contract_dialog_wraps_page3_decimal_quantization_in_local_context() -> None:
    dialog_source = DIALOG.read_text(encoding="utf-8")
    page_source = PAGE3.read_text(encoding="utf-8")

    # Les deux quantize historiques encore présents dans la page doivent être
    # exécutés via l'adaptateur Page3 du dialogue, jamais avec le contexte
    # Decimal global laissé par l'ancien runtime Teamworks.
    assert 'from decimal import localcontext' in dialog_source
    assert 'from Ctrl.CTRL_Creation_contrat_p3 import Page as LegacyPage3' in dialog_source
    assert 'class Page3(LegacyPage3):' in dialog_source
    assert 'def _MonthlySalaryDecimal(self):' in dialog_source
    assert 'def Validation(self):' in dialog_source
    assert dialog_source.count('context.prec = max(28, context.prec)') == 2
    assert page_source.count('.quantize(Decimal("0.01"))') >= 2


def test_modern_contract_hides_engine_managed_custom_fields() -> None:
    source = DIALOG.read_text(encoding="utf-8")

    assert 'from Ctrl.CTRL_Creation_contrat_p4 import Page as LegacyPage4' in source
    assert 'class Page4(LegacyPage4):' in source
    assert 'dialog.page3.IsCEESelected()' in source
    assert 'mots_cles_masques.add("BRUTJOUR")' in source
    assert 'dialog.page3.IsCCNSSelected()' in source
    assert 'mots_cles_masques.update(("HEBDO", "BRUTMENS"))' in source
    assert 'if mot_cle not in mots_cles_masques:' in source
    assert 'list_ctrl.dictChamps.pop(IDchamp, None)' in source
    # La liste est recalculée après validation du régime/type afin que le
    # passage CCNS <-> CEE soit immédiatement reflété à l'étape suivante.
    assert 'self.GetGrandParent().page4.MAJ_ListCtrl()' in source
