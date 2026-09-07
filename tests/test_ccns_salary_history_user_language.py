from pathlib import Path


HISTORY_DIALOG = Path("teamworks/Dlg/DLG_CCNS_salary_control_history.py")


def test_salary_history_does_not_expose_python_exception_text():
    source = HISTORY_DIALOG.read_text(encoding="utf-8")

    forbidden = (
        '"Impossible de comparer les snapshots.\\n\\n%s" % exc',
        '"Impossible de suivre les anomalies.\\n\\n%s" % exc',
        '"Impossible de générer les alertes.\\n\\n%s" % exc',
        '"Impossible de construire le rapport consolidé.\\n\\n%s" % exc',
    )

    for fragment in forbidden:
        assert fragment not in source, f"Détail technique encore exposé à l’utilisateur : {fragment}"


def test_salary_history_uses_business_language_in_user_visible_text():
    source = HISTORY_DIALOG.read_text(encoding="utf-8")

    forbidden_user_labels = (
        '"Snapshot : %s"',
        '"Sélectionnez exactement deux snapshots à comparer."',
        '"Un snapshot ne peut pas être comparé avec lui-même."',
        '"Sélectionnez exactement deux snapshots pour suivre les anomalies."',
        '"Sélectionnez au moins le snapshot courant à exporter."',
        '"Sélectionnez un snapshot courant, et éventuellement un snapshot précédent."',
    )

    for fragment in forbidden_user_labels:
        assert fragment not in source, f"Jargon technique encore visible dans l’interface RH : {fragment}"
