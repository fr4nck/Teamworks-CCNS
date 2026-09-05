import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_remboursement.py"


def _source():
    return DIALOG.read_text(encoding="utf-8")


def test_reimbursement_module_is_valid_python():
    ast.parse(_source())


def test_reimbursement_dialog_uses_semantic_sections_and_charter():
    source = _source()
    assert "wx.FlexGridSizer" not in source
    assert "wx.StaticBox" not in source
    assert ".Fit(self)" not in source
    assert "CTRL_Section.Section" in source
    assert "CTRL_Texte.Label" in source
    assert "CTRL_Texte.BodySecondary" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "wide")' in source
    assert 'UTILS_Interface.GetToken("surface_container_lowest")' in source
    assert "def AjusterColonnes" in source


def test_reimbursement_uses_one_checkbox_implementation_per_platform():
    source = _source()
    assert "_CheckboxFallback = object if _PHOENIX else CheckListCtrlMixin" in source
    assert "if _PHOENIX:\n            self.EnableCheckBoxes(True)\n        else:\n            CheckListCtrlMixin.__init__(self)" in source
    assert "self.IsItemChecked(index)" in source
    assert "self._set_checked(evt.Index, not self._is_checked(evt.Index))" in source
    assert "EVT_LIST_ITEM_CHECKED" in source
    assert "EVT_LIST_ITEM_UNCHECKED" in source


def test_reimbursement_statuses_use_only_semantic_families():
    source = _source()
    assert 'couleur = "success"' in source
    assert 'couleur = "warning"' in source
    assert 'couleur = "danger"' in source
    assert "wx.RED" not in source
    assert "wx.BLUE" not in source
    assert "wx.Colour(" not in source


def test_reimbursement_keeps_database_contract():
    source = _source()
    assert 'DB.ReqInsert("remboursements", listeDonnees, commit=False)' in source
    assert "UPDATE remboursements" in source
    assert "UPDATE deplacements SET IDremboursement=?" in source
    assert "UPDATE remboursements SET listeIDdeplacement=?" in source
    assert "DB.cursor.execute" in source
    assert "DB.Commit()" in source
    assert "DB.connexion.rollback()" in source
    assert "ListeItemsCoches" in source
    assert "montantRemboursement" in source
