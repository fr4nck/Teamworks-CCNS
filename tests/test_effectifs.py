"""Tests du premier lot ETP : données entièrement fictives."""
from datetime import date
from decimal import Decimal as D

import pytest

from domain.effectifs import (
    Categorie, ContratETP, Mesure, MoisRetenus, Profil, calculer_etp,
    profil_simulation, profils_comparaison,
)
from domain.repositories.ccns_data import CcnsContratRecord
from infrastructure.persistence.teamworks_etp_adapter import (
    categorie_historique, comparer_depuis_teamworks, convertir_contrats,
)


def contrat(numero, personne, categorie, debut="2025-01-01", fin="2025-12-31", heures="35", remplacement=None):
    return ContratETP(
        str(numero), str(personne), categorie,
        date.fromisoformat(debut), date.fromisoformat(fin) if fin else None,
        D(heures) if heures is not None else None, remplacement,
    )


def profil(**kwargs):
    options = {
        "code": "TEST", "version": "1", "libelle": "Simulation de test",
        "categories_incluses": frozenset({Categorie.CDI, Categorie.CDD, Categorie.CEE}),
    }
    options.update(kwargs)
    return Profil(**options)


def test_cdi_temps_plein_annuel():
    resultat = calculer_etp([contrat(1, 1, Categorie.CDI)], 2025, profil())
    assert resultat.total_brut == D("1")
    assert resultat.total_affiche == D("1.00")
    assert resultat.complet and not resultat.declarable
    assert len(resultat.mois) == 12
    assert resultat.mois[0].salaries[0].contrats == ("1",)


def test_temps_partiel_et_demi_annee():
    p = profil()
    mi_temps = calculer_etp([contrat(1, 1, Categorie.CDI, heures="17.5")], 2025, p)
    mi_annee = calculer_etp([contrat(2, 2, Categorie.CDI, fin="2025-06-30")], 2025, p)
    assert mi_temps.total_affiche == D("0.50")
    assert mi_annee.total_affiche == D("0.50")


def test_quatre_inclusions_cee_et_apprentissage():
    contrats = [
        contrat(1, 1, Categorie.CDI),
        contrat(2, 2, Categorie.CEE, heures="17.5"),
        contrat(3, 3, Categorie.APPRENTISSAGE),
    ]
    valeurs = [calculer_etp(contrats, 2025, p).total_affiche for p in profils_comparaison()]
    assert valeurs == [D("1.00"), D("1.50"), D("2.00"), D("2.50")]


def test_cee_sans_heures_exclu_ou_signale():
    donnees = [contrat(1, 1, Categorie.CDI), contrat(2, 2, Categorie.CEE, heures=None)]
    exclu = calculer_etp(donnees, 2025, profil_simulation(inclure_cee=False, inclure_apprentis=False))
    inclus = calculer_etp(donnees, 2025, profil_simulation(inclure_cee=True, inclure_apprentis=False))
    assert exclu.complet and exclu.exclus == ("2",)
    assert not inclus.complet and "HEURES_MANQUANTES" in {a.code for a in inclus.anomalies}


def test_prorata_jours_calendaires():
    resultat = calculer_etp(
        [contrat(1, 1, Categorie.CDI, debut="2025-01-16", fin="2025-01-31")], 2025, profil(),
    )
    assert resultat.mois[0].total == D(16) / D(31)
    assert resultat.total_brut == (D(16) / D(31)) / D(12)


def test_annee_bissextile():
    p = profil(annee_debut=2024)
    resultat = calculer_etp(
        [contrat(1, 1, Categorie.CDI, debut="2024-02-29", fin="2024-02-29")], 2024, p,
    )
    assert resultat.mois[1].total == D(1) / D(29)


def test_mois_avec_salaries_au_lieu_de_douze():
    janvier = [contrat(1, 1, Categorie.CDI, fin="2025-01-31")]
    annuel = calculer_etp(janvier, 2025, profil())
    actifs = calculer_etp(janvier, 2025, profil(mois_retenus=MoisRetenus.AVEC_SALARIES))
    assert annuel.total_affiche == D("0.08")
    assert annuel.diviseur == 12
    assert actifs.total_affiche == D("1.00") and actifs.diviseur == 1


def test_mesure_personnes_sans_horaire():
    p = profil(mesure=Mesure.PERSONNES)
    resultat = calculer_etp([contrat(1, 1, Categorie.CEE, heures=None)], 2025, p)
    assert resultat.complet and resultat.total_affiche == D("1.00")


def test_chevauchements_signales_et_plafonnes():
    contrats = [contrat(1, 1, Categorie.CDI), contrat(2, 1, Categorie.CDD)]
    resultat = calculer_etp(contrats, 2025, profil())
    assert resultat.total_affiche == D("1.00")
    assert not resultat.complet
    assert sum(a.code == "CONTRATS_CHEVAUCHANTS" for a in resultat.anomalies) == 1


def test_contrats_successifs_meme_personne_sans_double_compte():
    contrats = [
        contrat(1, 1, Categorie.CDD, fin="2025-01-15"),
        contrat(2, 1, Categorie.CDD, debut="2025-01-16", fin="2025-01-31"),
    ]
    resultat = calculer_etp(contrats, 2025, profil())
    assert resultat.mois[0].total == D("1")
    assert not resultat.anomalies


def test_remplacement_cdd_inconnu_bloque_si_exclusion_exigee():
    resultat = calculer_etp([contrat(1, 1, Categorie.CDD)], 2025, profil(exclure_cdd_remplacement=True))
    assert "REMPLACEMENT_INCONNU" in {a.code for a in resultat.anomalies}
    assert not resultat.complet


def test_cdd_remplacement_exclu_si_information_connue():
    resultat = calculer_etp(
        [contrat(1, 1, Categorie.CDI), contrat(2, 2, Categorie.CDD, remplacement=True)],
        2025, profil(exclure_cdd_remplacement=True),
    )
    assert resultat.complet
    assert resultat.exclus == ("2",)
    assert resultat.total_affiche == D("1.00")


def test_date_du_profil_hors_exercice_bloque():
    resultat = calculer_etp([contrat(1, 1, Categorie.CDI)], 2025, profil(annee_debut=2026))
    assert not resultat.complet
    assert "PROFIL_HORS_PERIODE" in {a.code for a in resultat.anomalies}


def test_decimal_strict_et_references():
    with pytest.raises(ValueError):
        profil(heures_temps_plein=D("NaN"))
    with pytest.raises(ValueError):
        profil(reglementaire_valide=True)
    with pytest.raises(ValueError):
        contrat(1, 1, Categorie.CDI, heures="-1")


def test_identifiant_contrat_duplique_bloque():
    resultat = calculer_etp(
        [contrat(1, 1, Categorie.CDI), contrat(1, 2, Categorie.CDI)], 2025, profil(),
    )
    assert not resultat.complet
    assert "CONTRAT_DUPLIQUE" in {a.code for a in resultat.anomalies}


def fiche(numero, personne, debut="2025-01-01", fin="2025-12-31", heures=35.0, typ="CDI"):
    return CcnsContratRecord(numero, personne, debut, fin, None, heures, None, "Ada", "Lovelace", None, typ)


@pytest.mark.parametrize("libelle,categorie", [
    ("CEE", Categorie.CEE),
    ("Contrat d’engagement éducatif", Categorie.CEE),
    ("Contrat d'apprentissage", Categorie.APPRENTISSAGE),
    ("Contrat à durée indéterminée", Categorie.CDI),
    ("Contrat de professionnalisation", Categorie.PROFESSIONNALISATION),
    ("CDII", Categorie.CDII),
    ("CDD remplacement maternité", Categorie.AUTRE),
])
def test_correspondance_types_stricte(libelle, categorie):
    assert categorie_historique(libelle) is categorie


def test_donnees_historiques_ambigues_bloquantes():
    donnees = [
        fiche(1, 1, debut="pas-une-date"),
        fiche(2, 2, typ="Un contrat mystère"),
        fiche(3, 3, fin=None, typ="CDD"),
        fiche(4, 4, heures=-2),
        fiche(5, 5),
    ]
    conversion = convertir_contrats(donnees)
    assert [c.id_contrat for c in conversion.contrats] == ["5"]
    assert {a.code for a in conversion.anomalies} == {
        "DATE_DEBUT_INVALIDE", "TYPE_NON_QUALIFIE", "FIN_CONTRAT_MANQUANTE", "HEURES_INVALIDES",
    }


def test_une_seule_lecture_de_base_pour_quatre_profils():
    class Lecteur:
        appels = 0
        def lire_contrats(self, limit=None):
            self.appels += 1
            return [fiche(1, 10), fiche(2, 11, heures=17.5, typ="CEE"), fiche(3, 12, typ="APPRENTISSAGE")]
    lecteur = Lecteur()
    resultats = comparer_depuis_teamworks(lecteur, 2025)
    assert lecteur.appels == 1
    assert [r.total_affiche for r in resultats] == [D("1.00"), D("1.50"), D("2.00"), D("2.50")]
    assert all(r.complet and not r.declarable for r in resultats)


def test_absence_dhoraire_propagee_uniquement_aux_profils_concernes():
    class Lecteur:
        def lire_contrats(self, limit=None):
            return [fiche(1, 10), fiche(2, 11, heures=None, typ="CEE")]
    resultats = comparer_depuis_teamworks(Lecteur(), 2025)
    assert resultats[0].complet
    assert not resultats[1].complet
    assert resultats[2].complet
    assert not resultats[3].complet


def test_inconnu_de_lecture_se_propage_a_tous_les_profils():
    class Lecteur:
        def lire_contrats(self, limit=None):
            return [fiche(1, 10), fiche(2, 11, typ="Intermittent hypothétique")]
    resultats = comparer_depuis_teamworks(Lecteur(), 2025)
    assert all("TYPE_NON_QUALIFIE" in {a.code for a in r.anomalies} for r in resultats)
    assert not any(r.complet for r in resultats)
