# TW-049 — Raccord de l'audit CCNS au contrôle salarial applicatif

## Objectif

L'audit réellement affiché dans Teamworks (`teamworks/CcnsCore/audit_contracts_ccns.py`) utilise désormais le contrôleur salarial applicatif introduit pour les contrats Teamworks réels. Le calcul historique parallèle du minimum salarial n'est plus appelé par l'audit.

## Assemblage retenu

1. `audit_contracts()` lit les contrats une seule fois via `CcnsDataReader.lire_contrats(limit=...)`.
2. Les enregistrements lus sont transmis à `TeamworksContractSalaryControlProvider` pour éviter une seconde lecture.
3. Les grilles Teamworks sont lues exclusivement via `CcnsDataReader.lire_grilles()` puis `CcnsDataReader.lire_lignes_grille(...)`.
4. Ces données sont converties vers les objets métier existants :
   - `SalaryGridCatalog` ;
   - `SalaryGridVersion` ;
   - `SalaryGridEntry` ;
   - `CCNSClassification` ;
   - `SalaryMinimumPeriodicity`.
5. `ContractSalaryControlControllerFactory.create_from_provider(...)` construit le même contrôleur que le chemin historique par `ContractRepository`, mais depuis un provider déjà créé.
6. Le contrôle est exécuté avec `create_smic_catalog_2026()` et `SmicTerritory.METROPOLITAN_FRANCE`.

## Conversions historiques partagées

Les conversions Teamworks communes ont été isolées dans `infrastructure/persistence/teamworks_contract_conversions.py` afin d'éviter l'import inverse du provider vers l'audit :

- dates historiques ;
- types de contrats ;
- régimes d'emploi ;
- organisation du temps.

Ce module neutre est partagé par l'audit et par `TeamworksContractSalaryControlProvider`.

## Traduction vers `AuditRow`

La structure publique de `AuditRow` reste inchangée. La traduction applique les règles suivantes :

- un contrat conforme ne crée aucune anomalie salariale ;
- un contrat non conforme reprend `issue_code` et `issue_message` du contrôleur ;
- un contrat non évaluable reçoit un code stable `CONTROLE_SALARIAL_NON_EVALUABLE_<REASON>` et conserve le message métier du contrôleur ;
- le motif historique `CONTRAT_A_DUREE_DETERMINEE_SANS_DATE_FIN` reste visible pour les CDD, CEE et autres contrats à durée déterminée historiques sans date de fin ;
- le contrôle d'ancienneté historique est conservé hors calcul du minimum salarial ;
- l'ordre et l'`IDcontrat` Teamworks restent ceux de la lecture historique.

## Compatibilité interface

Aucune modification wxPython n'est nécessaire. Les consommateurs existants de `AuditRow` continuent d'utiliser les mêmes champs :

- écran Audit CCNS ;
- liste Audit CCNS ;
- gadgets d'accueil ;
- synthèse individuelle ;
- ouverture des contrats via `IDcontrat`.

## Limites connues

- Le catalogue SMIC raccordé est celui de 2026 ; une date de référence hors période couverte propage l'erreur métier du contrôleur.
- Le catalogue de grilles construit pour l'audit utilise la grille Teamworks sélectionnée pour la date de référence afin d'éviter les chevauchements historiques ouverts.
