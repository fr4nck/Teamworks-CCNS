# Provider Teamworks réel pour le contrôle salarial

Le ticket TW-048 introduit `TeamworksContractSalaryControlProvider`, l'adaptateur d'infrastructure qui raccorde les contrats historiques Teamworks lus par `GestionDB` au port applicatif `ContractSalaryControlContractProvider`.

## Périmètre

Le provider :

- consomme exclusivement `CcnsDataReader.lire_contrats()` ;
- ne contient aucune requête SQL directe ;
- ne dépend pas de wxPython ;
- ne produit ni CSV ni JSON ;
- conserve l'ordre de lecture fourni par `CcnsDataReader` ;
- déduplique les contrats sur l'identifiant déterministe de contrat, sans réordonner les lignes conservées ;
- accepte les filtres applicatifs `contract_ids` et `employee_ids` sous forme de tuples d'`UUID` stricts.

## Identifiants historiques

Les identifiants Teamworks `IDcontrat` et `IDpersonne` sont transformés en UUID v5 stables avec deux espaces de noms distincts :

- `legacy_contract_uuid(IDcontrat)` pour les contrats ;
- `legacy_employee_uuid(IDpersonne)` pour les salariés.

Cette séparation garantit qu'une même valeur numérique historique ne peut pas produire le même UUID côté contrat et côté salarié.

## Conversions métier

Les conversions de type de contrat, régime d'emploi, organisation du temps et dates réutilisent les fonctions déjà présentes dans `teamworks/CcnsCore/audit_contracts_ccns.py`. Les champs salariaux historiques sont exposés au modèle `Contract` sans mutation :

- `salaire_base` alimente `base_salary_amount` et `monthly_gross_salary_amount` ;
- `temps_hebdo` alimente `weekly_reference_hours` et `weekly_hours` ;
- `classification` alimente `ccns_classification_code` et, lorsqu'elle est exploitable, une `CCNSClassification` minimale de même code.

## Contrats historiques incomplets

Un CDD, CEE, apprentissage, stage ou service civique sans date de fin est conservé dans le lot. Il n'est pas converti en CDI et n'est pas supprimé silencieusement.

Le contrat porte le motif stable `CONTRAT_A_DUREE_DETERMINEE_SANS_DATE_FIN`. Le service d'évaluation salariale le projette ensuite comme non évaluable avec le motif métier `historical_fixed_term_missing_end_date` et un message indiquant que ce contrat historique ne peut pas être évalué comme un CDI.

L'invariant général du domaine reste inchangé pour les nouveaux contrats valides : un contrat à durée déterminée sans date de fin reste refusé, sauf lorsqu'il porte explicitement ce motif d'import historique.
