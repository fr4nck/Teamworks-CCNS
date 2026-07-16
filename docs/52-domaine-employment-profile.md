# Domaine `EmploymentProfile`

`EmploymentProfile` décrit uniquement le régime métier applicable à un emploi.
Il s'agit d'un objet domaine immutable, sans dépendance à une interface, une
base de données, une API ou un contrat.

## Données portées

- un identifiant UUID ;
- un nom ;
- un `EmploymentRegime` ;
- les indicateurs de soumission à la CCNS, à la grille salariale, aux
  contrôles du temps de travail et aux contrôles CEE ;
- un indicateur d'activité.

L'énumération `EmploymentRegime` couvre au minimum les régimes `CCNS_STANDARD`,
`CEE`, `APPRENTICESHIP`, `CIVIC_SERVICE`, `INTERNSHIP`, `VOLUNTEER` et
`EXTERNAL_PROVIDER`. Les codes historiques déjà employés par les contrats sont
conservés pour assurer leur compatibilité.

## Réponses métier

Les méthodes `is_ccns`, `requires_salary_grid`,
`requires_working_time_controls` et `requires_cee_controls` exposent les
indicateurs du profil. Elles ne calculent aucune rémunération, durée ou règle
CCNS.

## Limites explicites

Le profil d'emploi ne représente pas le salarié, le contrat, le planning, la
rémunération, le groupe, le coefficient, la qualification, l'ancienneté, les
heures, les affectations ou les anomalies. Ces concepts restent portés par des
objets métier dédiés.
