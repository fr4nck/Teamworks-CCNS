# Objets conventionnels ajoutés

Cette étape ajoute au cœur Teamworks-CCNS les objets de base pour la partie conventionnelle :

- `CCNSClassification`
- `SalaryGrid`
- `SalaryGridLine`
- `MinimumType`
- premières structures de règles :
  - temps partiel court
  - ancienneté
  - CEE
  - préparation

## But

Préparer le terrain pour :
- les minima CCNS ;
- les groupes 1 à 8 ;
- les bases mensuelles / annuelles ;
- l'apprentissage ;
- les premières règles de calcul.

## Ce qui n'est pas encore branché

- la base de données ;
- la persistance ;
- le moteur de calcul complet ;
- l'injection automatique des valeurs CCNS.

## Régimes d'emploi canoniques

`EmploymentRegime` ne porte qu'un seul régime métier pour chaque situation.
Les codes historiques reçus par l'audit sont normalisés pendant le mapping :

| Code historique de type de contrat | Régime métier canonique |
| --- | --- |
| `APPRENTICESHIP` | `APPRENTICE` |
| `CIVIC_SERVICE` | `SERVICE_CIVIQUE` |
| `INTERNSHIP` | `STAGE_PFMP` |

Dans le périmètre actuel du domaine, `INTERNSHIP` et `STAGE_PFMP` ne sont pas
distingués comme deux situations juridiques : le premier est un code historique
de type de contrat et le second est le régime d'emploi canonique. Toute
distinction juridique future devra être documentée et accompagnée de tests avant
l'ajout d'un nouveau régime.
