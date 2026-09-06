import ast
from pathlib import Path

from teamworks.Utils.UTILS_ScenarioReports import ProtegerReportContreCycles


SOURCE_PATH = Path("teamworks/Dlg/DLG_Scenario.py")
GUARD_NAME = "ProtegerReportContreCycles"


def _source_tree():
    return ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))


def _decorator_names(method):
    names = []
    for decorator in method.decorator_list:
        if isinstance(decorator, ast.Name):
            names.append(decorator.id)
        elif isinstance(decorator, ast.Attribute):
            names.append(decorator.attr)
    return names


def _get_report_methods():
    tree = _source_tree()
    methods = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name in {"Tableau", "GetDictColonnes"}:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == "GetReportColonne":
                    methods[node.name] = child
                    break
    return methods


def test_report_cycle_guard_stops_a_to_b_to_a_recursion():
    class FakeReports:
        @ProtegerReportContreCycles
        def GetReportColonne(self, IDcategorie, IDpersonne, IDscenario):
            if IDscenario == 1:
                return self.GetReportColonne(20, IDpersonne, 2)
            return self.GetReportColonne(10, IDpersonne, 1)

    assert FakeReports().GetReportColonne(10, 7, 1) == (
        "+00:00",
        "ERREUR3",
        "",
    )


def test_report_cycle_guard_is_shared_across_both_report_engines():
    class FakeTableau:
        def __init__(self):
            self.total_engine = FakeGetDictColonnes(self)

        @ProtegerReportContreCycles
        def GetReportColonne(self, IDcategorie, IDpersonne, IDscenario):
            return self.total_engine.GetReportColonne(20, IDpersonne, 2)

    class FakeGetDictColonnes:
        def __init__(self, tableau):
            self.tableau = tableau

        @ProtegerReportContreCycles
        def GetReportColonne(self, IDcategorie, IDpersonne, IDscenario):
            return self.tableau.GetReportColonne(1000, IDpersonne, 1)

    assert FakeTableau().GetReportColonne(1000, 7, 1) == (
        "+00:00",
        "ERREUR3",
        "",
    )


def test_report_cycle_guard_preserves_acyclic_reports_and_resets_after_cycle():
    class FakeReports:
        @ProtegerReportContreCycles
        def GetReportColonne(self, IDcategorie, IDpersonne, IDscenario):
            if IDscenario == 1:
                return self.GetReportColonne(20, IDpersonne, 2)
            if IDscenario == 2 and IDcategorie == 20:
                return self.GetReportColonne(10, IDpersonne, 1)
            if IDscenario == 3:
                return self.GetReportColonne(40, IDpersonne, 4)
            return "+01:30", "Scénario final", ""

    reports = FakeReports()
    assert reports.GetReportColonne(10, 7, 1)[1] == "ERREUR3"
    assert reports.GetReportColonne(30, 7, 3) == (
        "+01:30",
        "Scénario final",
        "",
    )


def test_both_report_engines_are_protected_by_the_same_cycle_guard():
    methods = _get_report_methods()
    assert set(methods) == {"Tableau", "GetDictColonnes"}
    for class_name, method in methods.items():
        assert GUARD_NAME in _decorator_names(method), (
            f"{class_name}.GetReportColonne doit être protégé contre les cycles"
        )


def test_cycle_error_has_an_explicit_user_facing_message():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert 'label[6:] == "3"' in source
    assert "boucle de reports" in source.lower()
