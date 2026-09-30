from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_question.py"
SMOKE = ROOT / "tools" / "smoke_questionnaire_lifecycle.py"


def test_question_controls_target_the_owning_dialog_not_the_static_box():
    source = DIALOG.read_text(encoding="utf-8")

    assert "owner = self.GetParent().GetParent()" in source
    assert "owner.ctrl_hauteur" in source
    assert "owner.ctrl_valmin" in source
    assert "owner.ctrl_valmax" in source
    assert "owner.ActiveCtrlChoix" in source
    assert "owner.MAJ_apercu" in source


def test_questionnaire_smoke_constructs_a_new_question_dialog():
    source = SMOKE.read_text(encoding="utf-8")

    assert "TEAMWORKS_SMOKE_QUESTIONNAIRE_STAGE:new-question-dialog" in source
    assert "DLG_Saisie_question" in source
    assert "_smoke_saisie_question.Dialog(" in source
    assert 'type="individu", IDquestion=None' in source
    assert "ctrl_hauteur is not None" in source
    assert "ctrl_valmin is not None" in source
    assert "ctrl_valmax is not None" in source
