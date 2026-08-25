from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / "teamworks" / "Dlg" / "DLG_Selection_mails.py"


def test_manual_mail_selection_uses_shared_mailing_core():
    source = SELECTION.read_text(encoding="utf-8")

    assert "from Utils import UTILS_Mailing" in source
    assert "UTILS_Mailing.SplitEmailAddresses(self.ctrl.GetValue())" in source
    assert "[a-zA-Z]{2,3}" not in source


def test_people_mail_selection_normalizes_and_validates_addresses():
    source = SELECTION.read_text(encoding="utf-8")

    assert "adresses = UTILS_Mailing.SplitEmailAddresses(track.email)" in source
    assert "listeAdresses.extend(adresses)" in source
    assert "if not UTILS_Mailing.SplitEmailAddresses(track.email):" in source
    assert "adresse.casefold()" in source
