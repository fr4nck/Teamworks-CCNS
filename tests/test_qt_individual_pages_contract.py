from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "poc" / "qt-theme" / "individual_pages.py"
TABS = ROOT / "poc" / "qt-theme" / "legacy_individual_tabs.py"
DIALOGS = ROOT / "poc" / "qt-theme" / "scenario_expense_dialogs.py"


def _class_assignments(path: Path, class_name: str) -> dict[str, object]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            values: dict[str, object] = {}
            for statement in node.body:
                if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
                    continue
                target = statement.targets[0]
                if isinstance(target, ast.Name):
                    try:
                        values[target.id] = ast.literal_eval(statement.value)
                    except (ValueError, TypeError):
                        pass
            return values
    raise AssertionError(f"classe {class_name} introuvable dans {path}")


def test_scenarios_columns_match_historical_individual_page() -> None:
    values = _class_assignments(PAGES, "ScenariosPage")
    assert values["HEADERS"] == ("Nom du scénario", "Période", "Description")


def test_expenses_columns_match_historical_individual_page() -> None:
    values = _class_assignments(PAGES, "ExpensesPage")
    assert values["TRIP_HEADERS"] == (
        "N°",
        "Date",
        "Objet",
        "Trajet",
        "Distance",
        "Tarif",
        "Montant",
        "Remboursement",
    )
    assert values["REIMBURSEMENT_HEADERS"] == (
        "N°",
        "Date",
        "Montant",
        "Déplacements rattachés",
    )


def test_legacy_tabs_delegate_scenarios_and_expenses_to_common_pages() -> None:
    source = TABS.read_text(encoding="utf-8")
    assert "self.scenarios_page = ScenariosPage(self.icon_loader)" in source
    assert "return self.scenarios_page" in source
    assert "self.expenses_page = ExpensesPage(self.icon_loader)" in source
    assert "return self.expenses_page" in source
    assert '"État"' not in source
    assert '"Rmbst"' not in source


def test_scenarios_and_expenses_use_dedicated_source_grounded_dialogs() -> None:
    source = PAGES.read_text(encoding="utf-8")
    assert "from scenario_expense_dialogs import" in source
    assert "ScenarioPreviewDialog" in source
    assert "TripPreviewDialog" in source
    assert "ReimbursementPreviewDialog" in source


def test_reimbursement_dialog_columns_match_historical_attachment_list() -> None:
    values = _class_assignments(DIALOGS, "ReimbursementPreviewDialog")
    assert values["TRIP_HEADERS"] == (
        "N°",
        "Date",
        "Objet",
        "Trajet",
        "Distance",
        "Tarif",
        "Montant",
    )


def test_scenario_dialog_does_not_invent_static_business_grid_axes() -> None:
    source = DIALOGS.read_text(encoding="utf-8")
    assert 'QTableWidget(0, 0)' in source
    assert '["Période", "Catégorie", "Temps"]' not in source
    assert '"Personne sélectionnée"' not in source
