from pathlib import Path


AUDIT_DIALOG = Path("teamworks/Dlg/DLG_CCNS_audit_list.py")


def test_ccns_audit_never_interpolates_exception_text_in_user_messages():
    source = AUDIT_DIALOG.read_text(encoding="utf-8")

    forbidden = (
        '"Une erreur est survenue pendant l\'audit CCNS.\\n\\n%s" % exc',
        '"Impossible de construire la synthèse salariale depuis l\'audit chargé.\\n\\n%s" % exc',
        '"Impossible d\'enregistrer l\'historique du contrôle salarial.\\n\\n%s" % exc',
        '"Impossible d\'exporter le fichier CSV.\\n\\n%s" % exc',
        'errors.append("Dialog(IDcontrat=...): %s" % exc)',
        'errors.append("CTRL(IDcontrat=...): %s" % exc)',
        '"Tentatives effectuées :\\n- " + "\\n- ".join(errors)',
    )

    for fragment in forbidden:
        assert fragment not in source, f"Détail technique encore exposé à l'utilisateur : {fragment}"


def test_ccns_audit_keeps_diagnostics_in_logs_not_user_messages():
    source = AUDIT_DIALOG.read_text(encoding="utf-8")
    assert "import logging" in source
    assert "LOGGER = logging.getLogger(__name__)" in source
    assert 'LOGGER.exception("Échec de l\'audit CCNS")' in source
    assert 'LOGGER.exception("Échec de construction de la synthèse salariale")' in source
    assert 'LOGGER.exception("Échec d\'enregistrement de l\'historique du contrôle salarial")' in source
    assert 'LOGGER.exception("Échec d\'export CSV de l\'audit CCNS")' in source


def test_ccns_audit_does_not_expose_snapshot_internal_identifier():
    source = AUDIT_DIALOG.read_text(encoding="utf-8")
    assert '"Contrôle salarial enregistré.\\n\\nSnapshot : %s"' not in source
    assert '"Contrôle salarial enregistré dans l\'historique."' in source
