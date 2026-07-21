# TW-027 — Contrôle d'une rémunération au regard du minimum CCNS

Le contrôle de rémunération CCNS est porté par un service de domaine pur et stateless. Il reçoit explicitement le groupe de classification, la date de référence, la rémunération brute de référence, sa périodicité et la durée hebdomadaire contractuelle. Il ne lit pas la persistance, ne consulte pas l'interface graphique et n'utilise jamais la date courante.

## Sélection de la grille

Le minimum applicable est sélectionné par `SalaryGridCatalog.version_applicable_on(reference_date)`. Les périodes des versions de grille restent inclusives et aucune grille historique n'est écrasée. Si aucune version n'est applicable à la date demandée, l'erreur métier du catalogue est propagée.

Le service utilise ensuite uniquement l'entrée du groupe dans la version sélectionnée. Il ne recherche pas le groupe dans une autre version et ne met en place aucun repli silencieux.

## Périodicité des minima

La rémunération fournie doit déjà être exprimée dans la même périodicité que le minimum conventionnel :

- groupes 1 à 6 : minimum mensuel et rémunération mensuelle brute ;
- groupes 7 et 8 : minimum annuel et rémunération annuelle brute.

Une incohérence de périodicité est refusée. Le contrôle ne convertit pas un salaire mensuel en annuel, un salaire annuel en mensuel, un salaire horaire en mensuel ou un salaire mensuel en horaire.

## Proratisation mensuelle des groupes 1 à 6

La référence temps plein est strictement `Decimal("35.00")` heures hebdomadaires.

Pour les minima mensuels :

- à 35 heures ou plus, le minimum exigé reste le minimum temps plein ;
- en dessous de 35 heures, le minimum est proratisé sur 35 heures ;
- pour une durée strictement inférieure à 24 heures, la majoration conventionnelle de temps partiel est ajoutée via `increase_rate_for_weekly_hours()`.

Formule appliquée sous 35 heures :

```text
minimum_exige = minimum_temps_plein × heures_hebdomadaires / Decimal("35.00") × (Decimal("1.00") + taux_majoration)
```

Les taux restent des `Decimal` :

- 5 % est représenté par `Decimal("0.05")` pour 10 heures ou moins ;
- 2 % est représenté par `Decimal("0.02")` pour plus de 10 heures et strictement moins de 24 heures ;
- 24 heures ou plus ne déclenche aucune majoration.

Il n'y a pas de sur-proratisation ni de majoration lorsque la durée hebdomadaire est supérieure ou égale à 35 heures.

## Groupes 7 et 8

Pour les minima annuels des groupes 7 et 8, le contrôle compare directement la rémunération annuelle au minimum annuel de la grille. Dans ce ticket, aucune proratisation annuelle selon les heures hebdomadaires et aucune majoration temps partiel ne sont appliquées. La durée hebdomadaire reste enregistrée dans le résultat pour expliquer l'entrée contrôlée.

## Montants, arrondi et écart

Tous les montants calculés restent des `Decimal`, sont quantifiés à `Decimal("0.01")` et utilisent `ROUND_HALF_UP`. Aucun calcul ne passe par `float`.

La convention de signe de l'écart est :

```text
difference_amount = remuneration_amount - required_minimum_amount
```

Conséquences :

- écart positif : rémunération supérieure au minimum ;
- écart nul : rémunération exactement égale au minimum, donc conforme ;
- écart négatif : rémunération insuffisante.

## Limites explicites

Ce service ne calcule pas une paie complète. Il ne traite pas la rémunération nette, les primes, la prime d'ancienneté, les avantages en nature, les heures supplémentaires ou complémentaires, les absences, congés, arrêts maladie, rappels de salaire, conversions de périodicité, treizième mois, rémunération variable, polyvalence, reclassification automatique, SMIC, persistance, interface utilisateur, alertes ou correction automatique de contrat.

Les objets de contrat existants ne sont pas adaptés dans ce ticket : ils portent encore des montants et durées optionnels en `float`, alors que le contrôle exige des `Decimal` stricts et toutes les données explicites. La méthode `evaluate(...)` reste donc l'unique point d'entrée pour éviter de créer un second concept concurrent ou une conversion implicite.
