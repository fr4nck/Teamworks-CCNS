# TW-058 — Alertes salariales CCNS

Les alertes salariales servent à afficher rapidement les situations nécessitant une action de direction ou de comptabilité. Elles sont générées en lecture seule à partir du dernier snapshot salarial, de sa comparaison avec le snapshot précédent et du suivi des anomalies.

## Sources utilisées

Le service de domaine `GenerateContractSalaryAlertsService` ne lit aucune base, ne connaît pas wxPython et ne lance aucun contrôleur salarial. Il consomme uniquement :

- le snapshot courant historisé ;
- la comparaison entre le snapshot précédent et le snapshot courant ;
- l'historique des anomalies produit pour les mêmes snapshots.

## Gravités

- `CRITICAL` : situation qui nécessite une action prioritaire, par exemple nouveau contrat non conforme, contrat devenu non conforme, anomalie persistante aggravée ou écart salarial en hausse.
- `WARNING` : point de vigilance, par exemple nouvelle anomalie, contrat non évalué, minimum conventionnel augmenté ou baisse de rémunération.
- `INFO` : information de suivi, par exemple anomalie résolue, contrat redevenu conforme, nouveau contrat conforme ou contrat supprimé.

## Types

Les types publics sont :

- `NEW_ANOMALY` ;
- `PERSISTENT_ANOMALY` ;
- `SALARY_DECREASE` ;
- `MINIMUM_INCREASE` ;
- `NON_COMPLIANT_CONTRACT` ;
- `NOT_EVALUATED_CONTRACT` ;
- `NEW_CONTRACT` ;
- `REMOVED_CONTRACT` ;
- `SIGNIFICANT_SHORTFALL` ;
- `OTHER`.

## Règles de génération

Les seuils sont centralisés dans le domaine :

- `SIGNIFICANT_SHORTFALL_INCREASE_THRESHOLD` ;
- `MINIMUM_INCREASE_THRESHOLD` ;
- `SALARY_DECREASE_THRESHOLD`.

Aucune valeur magique n'est utilisée dans les règles. Les montants restent des `Decimal`.

Le générateur produit notamment :

- une alerte critique lorsqu'un nouveau contrat est non conforme ;
- une alerte critique lorsqu'un contrat devient non conforme ;
- une alerte critique lorsque l'écart salarial augmente ;
- une alerte critique lorsqu'une anomalie persistante s'aggrave ;
- une alerte d'avertissement pour une nouvelle anomalie ;
- une alerte d'avertissement pour un contrat devenu non évalué ;
- une alerte d'avertissement pour une hausse du minimum applicable ;
- une alerte d'avertissement pour une baisse de rémunération ;
- une alerte d'information pour une anomalie résolue ;
- une alerte d'information pour un contrat redevenu conforme ;
- une alerte d'information pour un nouveau contrat conforme ;
- une alerte d'information pour un contrat supprimé.

L'ordre est déterministe : gravité décroissante, identifiant de contrat, type, puis clé de résumé.

## Présentation et interface

Les textes restent hors domaine. Le présentateur `ContractSalaryAlertPresenter` transforme les clés métier en libellés français et expose un résumé avec le nombre total d'alertes, les critiques, les avertissements et les informations.

Depuis l'historique salarial wxPython, le bouton **Alertes** affiche une vue en lecture seule avec les colonnes utiles : gravité, salarié, contrat, type, résumé et date. Les filtres disponibles couvrent toutes les alertes, critiques, warnings, informations, non-conformités, nouvelles anomalies et alertes résolues.

## Différence avec le suivi des anomalies

Le suivi des anomalies décrit l'évolution d'une anomalie entre deux snapshots : nouvelle, persistante, résolue ou remplacée. Les alertes sont une synthèse opérationnelle plus large : elles réutilisent ce suivi, mais ajoutent aussi les signaux issus de la comparaison des snapshots, comme les nouveaux contrats, les suppressions, les baisses de rémunération et les hausses de minimum.

## Limites

- Aucun recalcul salarial n'est effectué.
- Aucun snapshot n'est modifié.
- Aucune notification externe n'est envoyée.
- Aucun export consolidé n'est produit dans cette TW.
- Les noms de salariés ne sont pas enrichis par accès base ; seul l'identifiant salarié déjà présent dans les snapshots est affiché.
