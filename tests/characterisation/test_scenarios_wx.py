"""Caractérisation du moteur Scénarios wxPython avant transposition Qt."""

from __future__ import annotations

import pytest

from source_legacy import (
    column_names,
    compact_whitespace,
    db_data_schema,
    function_node,
    function_source,
    load_method_as_function,
)


SCENARIO = "teamworks/Dlg/DLG_Scenario.py"
GESTION = "teamworks/Dlg/DLG_Scenario_gestion.py"
SAISIE_REPORT = "teamworks/Dlg/DLG_Scenario_saisie_report.py"


def test_schema_scenario_et_categories_est_sans_contrainte_relationnelle() -> None:
    assert column_names("scenarios") == [
        "IDscenario",
        "IDpersonne",
        "nom",
        "description",
        "mode_heure",
        "detail_mois",
        "date_debut",
        "date_fin",
        "toutes_categories",
    ]
    assert column_names("scenarios_cat") == [
        "IDscenario_cat",
        "IDscenario",
        "IDcategorie",
        "prevision",
        "report",
        "date_debut_realise",
        "date_fin_realise",
    ]
    declarations = [
        str(column[1]).upper()
        for table in ("scenarios", "scenarios_cat")
        for column in db_data_schema(table)
    ]
    assert not any("FOREIGN KEY" in declaration for declaration in declarations)
    assert not any("REFERENCES" in declaration for declaration in declarations)
    assert not any("CHECK" in declaration for declaration in declarations)


def test_codage_des_reports_manuels_et_automatiques() -> None:
    source = function_source(SAISIE_REPORT, "GetReport", class_name="MyDialog")
    assert 'M%s%02d:%02d' in source
    assert 'A%d;%d' in source
    assert 'minutes = minutes * 60 // 100' in source


def test_choix_automatique_reste_limite_a_la_meme_personne_et_exclut_le_scenario_courant() -> None:
    source = compact_whitespace(
        function_source(SAISIE_REPORT, "GetTracks", class_name="ListView")
    )
    assert "WHERE IDpersonne=%d AND IDscenario!=%d ORDER BY date_debut" in source
    assert "WHERE IDpersonne=%d ORDER BY date_debut" in source


def test_report_automatique_transporte_scenario_et_categorie_dans_une_chaine() -> None:
    source = function_source(SCENARIO, "GetValeursColonne", class_name="Tableau")
    assert 'report[1:].split(";")' in source
    assert "self.GetReportColonne(" in source
    assert 'dictDonnees["report"] = "%s;%s;%s;%s"' in source


def test_reports_automatiques_sont_resolus_recursivement_sans_contexte_de_cycle() -> None:
    node = function_node(SCENARIO, "GetReportColonne", class_name="Tableau")
    assert [argument.arg for argument in node.args.args] == [
        "self",
        "IDcategorie",
        "IDpersonne",
        "IDscenario",
    ]
    source = function_source(SCENARIO, "GetReportColonne", class_name="Tableau")
    assert "self.GetValeursColonne(" in source
    assert "modeReport=True" in source
    assert "visited" not in source.lower()
    assert "cycle" not in source.lower()


def test_report_total_reutilise_la_colonne_totale_du_scenario_source() -> None:
    source = function_source(SCENARIO, "GetReportColonne", class_name="Tableau")
    assert "if IDcategorie == 1000" in source
    assert "GetDictColonneTotal()" in source


def test_reference_absente_ou_autre_personne_devient_zero_avec_marqueur_erreur() -> None:
    source = function_source(SCENARIO, "GetReportColonne", class_name="Tableau")
    assert '"+00:00", "ERREUR2", ""' in source
    assert '"+00:00", "ERREUR1", ""' in source
    assert "if IDpersonne != reportIDpersonne" in source


def test_erreurs_de_report_affichees_bloquent_la_sauvegarde_du_dialogue() -> None:
    tableau = function_source(SCENARIO, "InitTableau", class_name="Tableau")
    validation = function_source(SCENARIO, "OnBoutonOk", class_name="Dialog")
    assert 'label.startswith("ERREUR")' in tableau
    assert "self.nbreErreursReport += 1" in tableau
    assert "self.ctrl_tableau.nbreErreursReport > 0" in validation
    assert validation.index("self.ctrl_tableau.nbreErreursReport > 0") < validation.index(
        "self.Sauvegarde()"
    )


def test_duplication_copie_les_reports_et_periodes_sans_recriture() -> None:
    source = function_source(GESTION, "OnBoutonDupliquer", class_name="Panel")
    assert '_(u"Copie de %s") % nom' in source
    assert '("report", report)' in source
    assert '("date_debut_realise", date_debut_realise)' in source
    assert '("date_fin_realise", date_fin_realise)' in source
    assert 'DB.ReqInsert("scenarios_cat", listeDonnees)' in source


def test_suppression_reste_autorisee_apres_avertissement_et_ne_repare_pas_les_dependances() -> None:
    source = function_source(GESTION, "Supprimer", class_name="Panel")
    assert 'report[1:].split(";")' in source
    assert "nbreReports" in source
    assert 'DB.ReqDEL("scenarios", "IDscenario", IDscenario)' in source
    assert 'DB.ReqDEL("scenarios_cat", "IDscenario", IDscenario)' in source
    assert "ReqMAJ" not in source


def test_sauvegarde_synchronise_la_virtualdb_avec_scenarios_cat() -> None:
    source = function_source(SCENARIO, "Sauvegarde", class_name="Dialog")
    assert 'DB.ReqInsert("scenarios", listeDonnees)' in source
    assert 'DB.ReqMAJ("scenarios", listeDonnees' in source
    assert 'DB.ReqInsert("scenarios_cat", listeDonnees)' in source
    assert 'DB.ReqMAJ("scenarios_cat", listeDonnees' in source
    assert 'DB.ReqDEL("scenarios_cat", "IDscenario_cat", IDscenario_cat)' in source


def test_operation_heures_conserve_le_resultat_historique_usuel() -> None:
    operation = load_method_as_function(SCENARIO, "Tableau", "OperationHeures")
    assert operation(object(), "+10:00", "+02:30", "addition") == "+12:30"
    assert operation(object(), "+02:00", "+00:30", "soustraction") == "+1:30"


@pytest.mark.xfail(
    strict=True,
    reason="défaut historique : une durée négative inférieure à une heure perd son signe",
)
def test_soustraction_negative_inferieure_a_une_heure_conserve_son_signe() -> None:
    operation = load_method_as_function(SCENARIO, "Tableau", "OperationHeures")
    assert operation(object(), "+00:00", "+00:30", "soustraction") == "-0:30"
