from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / "teamworks" / "Dlg" / "DLG_Selection_type_document.py"
MAILMERGE = ROOT / "teamworks" / "Dlg" / "DLG_Publiposteur.py"
CONTRACT_MAILMERGE = ROOT / "teamworks" / "Dlg" / "DLG_Publiposteur_contrat.py"


def test_document_type_dialog_preserves_preview_height_and_requested_size() -> None:
    source = SELECTION.read_text(encoding="utf-8")

    assert "size=size" in source
    assert "bitmap.GetWidth() + 12" in source
    assert "bitmap.GetHeight() + 12" in source
    assert "wx.ALIGN_CENTER_HORIZONTAL" in source
    assert "sizer_base.Add(self," not in source


def test_mailmerge_list_keeps_staticbox_parent_and_page_controller_distinct() -> None:
    source = MAILMERGE.read_text(encoding="utf-8")

    assert "ListCtrl_fichiers(self.sizer_choix_staticbox, controller=self)" in source
    assert "def __init__(self, parent, controller=None):" in source
    assert "self.parent = controller or parent" in source
    assert "choixModele = self.parent.choixModele" in source
    assert "self.parent.choixLogiciel" in source


def test_contract_mailmerge_list_forwards_the_page_controller() -> None:
    source = CONTRACT_MAILMERGE.read_text(encoding="utf-8")

    assert "def __init__(self, parent, controller=None):" in source
    assert "super(ListCtrl_fichiers, self).__init__(parent, controller=owner)" in source
