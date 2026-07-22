# TW-037 — Requête de consultation du contrôle salarial

`ContractSalaryControlQueryService` applique une requête pure sur une `ContractSalaryControlProjection` déjà calculée. Il ne recalcule ni minima, ni conformité, ni écarts, ni anomalies, et conserve les instances de `ContractSalaryControlRow`.

## Filtres

`ContractSalaryControlQuery` est immutable et combine tous les critères par ET logique. Les valeurs d'un même tuple sont combinées par OU. Un tuple vide signifie aucun filtre.

Filtres disponibles : statuts, salariés, contrats, classifications, sources de minimum, territoires, motifs d'échec, présence de manque salarial, bornes minimales/maximales de manque salarial et recherche textuelle.

Les tuples doivent être stricts, typés, sans doublons. Les montants sont des `Decimal` stricts, positifs ou nuls, quantifiés à deux décimales.

## Recherche textuelle

`search_text` est optionnel, trimé, non vide après normalisation et comparé sans tenir compte de la casse. La recherche est littérale, sans expression régulière, uniquement sur `classification_code`, `failure_message`, `issue_code` et `issue_message`. Les UUID, dates, montants et noms de salariés ne sont pas transformés en texte.

## Tri

`ContractSalaryControlSortField.SOURCE_ORDER` préserve l'ordre source en ascendant et inverse l'ordre source en descendant. Les autres tris utilisent des valeurs stables : valeur d'enum, entier UUID, `Decimal` natif ou chaîne métier non traduite. Les `None` sont ordonnés explicitement après les valeurs renseignées en ascendant. En cas d'égalité, l'ordre source sert de critère secondaire.

## Pagination

La requête applique toujours : filtres, tri, puis pagination. `offset` est un `int` strict positif ou nul. `limit` est `None` ou un `int` strictement positif. Lorsque `limit` vaut `None`, toutes les lignes filtrées à partir de `offset` sont retournées ; `has_next_page` est donc faux une fois ces lignes retournées, et `previous_offset` recule de la taille effectivement retournée.

## Page

`ContractSalaryControlPage.filtered_rows` contient toutes les lignes filtrées et triées avant pagination. `rows` contient seulement la page retournée. Les compteurs, `total_shortfall_amount` et `valid` portent sur `filtered_rows`. Une page filtrée vide est valide.

## Limites volontaires

La requête n'ajoute ni persistance, ni repository, ni API, ni interface graphique, ni export, ni SQL, ni cache, ni tri localisé, ni recherche floue, ni correction automatique et ni recalcul salarial.
