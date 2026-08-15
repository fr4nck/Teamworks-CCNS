from pathlib import Path


def test_email_attachments_selection_and_dialog_guards():
    source = Path("teamworks/Ol/OL_Pieces_jointes_emails.py").read_text(encoding="utf-8")

    assert "selections = self.Selection()" in source
    assert "selection = selections[0] if selections else None" in source
    assert "selection = self.Selection()" in source
    assert "track = selection[0]" in source
    assert "self.Selection()[0]" not in source

    cancel_block = "else:\n            dlg.Destroy()\n            return"
    assert cancel_block in source
