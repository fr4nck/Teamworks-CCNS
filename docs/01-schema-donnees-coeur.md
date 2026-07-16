# Schéma de données du cœur

Le cœur Teamworks s’organise autour de quatre ensembles principaux :

1. personnes et profils ;
2. contrats et cadres d’emploi ;
3. activité et affectations ;
4. règles, résultats de calcul et anomalies.

Objets à poser en premier :
- personne
- profil_juridique
- type_contrat
- regime_emploi
- organisation_temps
- contrat
- classification_ccns
- grille_salariale
- ligne_grille_salariale
- affectation
- regle_calcul
- calcul_resultat
- anomalie

## Contrat

Le type de contrat distingue notamment `CDI`, `CDII`, `CDD`, `CEE`, `APPRENTICESHIP`,
`INTERNSHIP` et `CIVIC_SERVICE`. Seuls le CDI et le CDII peuvent ne pas avoir de
date de fin ; les autres types exigent une date de fin.

La date de signature (`signature_date`) est facultative. Lorsqu'elle est renseignée,
elle doit être une date valide. Le domaine ne compare pas cette date à la date de
début et ne calcule aucun délai légal de signature.
