from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPRESSION_FRAIS = ROOT / "teamworks" / "Dlg" / "DLG_Impression_frais.py"
SAISIE_DEPLACEMENT = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_deplacement.py"
SAISIE_REMBOURSEMENT = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_remboursement.py"
GESTION_SCENARIOS = ROOT / "teamworks" / "Dlg" / "DLG_Scenario_gestion.py"
SCENARIO = ROOT / "teamworks" / "Dlg" / "DLG_Scenario.py"


def _methode(source, debut_signature, fin_signature):
    debut = source.index(debut_signature)
    fin = source.index(fin_signature, debut)
    return source[debut:fin]


def test_cocher_un_deplacement_ne_modifie_jamais_la_table_gadgets():
    source = IMPRESSION_FRAIS.read_text(encoding="utf-8")
    methode = _methode(
        source,
        "    def OnCheckItem(self, index, flag):",
        "    def Importation(self):",
    )
    assert 'ReqMAJ("gadgets"' not in methode


def test_supprimer_un_scenario_reference_ne_peut_pas_creer_de_report_orphelin():
    source = GESTION_SCENARIOS.read_text(encoding="utf-8")
    methode = _methode(
        source,
        "    def Supprimer(self):",
        "    def OnBoutonDupliquer(self, event):",
    )

    # Tant qu'aucun mécanisme de cascade/réécriture atomique n'existe, la stratégie
    # sûre pour la 0.9.2 est de refuser la suppression d'un scénario référencé.
    assert "Souhaitez-vous tout de même le supprimer" not in methode


def test_suppression_scenario_est_atomique():
    source = GESTION_SCENARIOS.read_text(encoding="utf-8")
    methode = _methode(
        source,
        "    def Supprimer(self):",
        "    def OnBoutonDupliquer(self, event):",
    )
    assert "commit=False" in methode
    assert methode.count("DB.Commit()") <= 1


def test_cache_distance_conserve_les_codes_postaux_sur_cinq_caracteres():
    source = SAISIE_DEPLACEMENT.read_text(encoding="utf-8")
    methode = _methode(
        source,
        "    def SauvegardeDistance(self):",
        "    def GetPersonne(self):",
    )
    assert "int(self.ctrl_cp_depart.GetValue())" not in methode
    assert "int(self.ctrl_cp_arrivee.GetValue())" not in methode


def test_impression_frais_n_utilise_pas_float_pour_les_montants():
    source = IMPRESSION_FRAIS.read_text(encoding="utf-8")
    assert "float(distance) * float(tarif_km)" not in source


def test_rattachement_remboursement_n_utilise_pas_egalite_exacte_sur_float():
    source = SAISIE_REMBOURSEMENT.read_text(encoding="utf-8")
    assert "montantNonRattache == 0" not in source


def test_rattachement_remboursement_n_accumule_pas_les_montants_en_float():
    source = SAISIE_REMBOURSEMENT.read_text(encoding="utf-8")
    methode = _methode(
        source,
        "    def MajLabelRattachement(self):",
        "    def Importation(self):",
    )
    assert "montant = float(" not in methode


def test_sauvegarde_scenario_est_une_transaction_unique():
    source = SCENARIO.read_text(encoding="utf-8")
    methode = _methode(source, "    def Sauvegarde(self):", "    def OnBoutonExcel(self, event):")
    assert "commit=False" in methode
    assert methode.count("DB.Commit()") <= 1


def test_duplication_scenario_est_une_transaction_unique():
    source = GESTION_SCENARIOS.read_text(encoding="utf-8")
    methode = _methode(
        source,
        "    def OnBoutonDupliquer(self, event):",
        "    def MAJ_ListCtrl(self, IDselection=None):",
    )
    assert "commit=False" in methode
    assert methode.count("DB.Commit()") <= 1


def test_presence_scenario_utilise_le_contrat_horaire_de_journee():
    source = SCENARIO.read_text(encoding="utf-8")
    methode = _methode(
        source,
        "    def GetHeuresRealisees(self, IDpersonne=None, date_debut_periode=None, date_fin_periode=None, IDcategorie=None, mode_detail=None):",
        "    def GetCategoriesUtilisees(self, IDpersonne, date_debut, date_fin):",
    )
    assert "duree_presence_wx(" in methode
    assert 'OperationHeures("+" + heure_fin, "+" + heure_debut, "soustraction")' not in methode


def test_presence_scenario_ne_concatene_pas_none_aux_horaires():
    source = SCENARIO.read_text(encoding="utf-8")
    methode = _methode(
        source,
        "    def GetHeuresRealisees(self, IDpersonne=None, date_debut_periode=None, date_fin_periode=None, IDcategorie=None, mode_detail=None):",
        "    def GetCategoriesUtilisees(self, IDpersonne, date_debut, date_fin):",
    )
    assert '"+" + heure_fin' not in methode
    assert '"+" + heure_debut' not in methode
