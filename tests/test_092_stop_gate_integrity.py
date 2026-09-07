from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPRESSION_FRAIS = ROOT / "teamworks" / "Dlg" / "DLG_Impression_frais.py"
GESTION_SCENARIOS = ROOT / "teamworks" / "Dlg" / "DLG_Scenario_gestion.py"


def test_cocher_un_deplacement_ne_modifie_jamais_la_table_gadgets():
    source = IMPRESSION_FRAIS.read_text(encoding="utf-8")
    debut = source.index("    def OnCheckItem(self, index, flag):")
    fin = source.index("    def Importation(self):", debut)
    methode = source[debut:fin]
    assert 'ReqMAJ("gadgets"' not in methode


def test_supprimer_un_scenario_reference_ne_peut_pas_creer_de_report_orphelin():
    source = GESTION_SCENARIOS.read_text(encoding="utf-8")
    debut = source.index("    def Supprimer(self):")
    fin = source.index("    def OnBoutonDupliquer(self, event):", debut)
    methode = source[debut:fin]

    # Tant qu'aucun mécanisme de cascade/réécriture atomique n'existe, la stratégie
    # sûre pour la 0.9.2 est de refuser la suppression d'un scénario référencé.
    assert "Souhaitez-vous tout de même le supprimer" not in methode
