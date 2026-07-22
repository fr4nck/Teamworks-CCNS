# Tableau de bord salarial CCNS

## Rôle

Le tableau de bord salarial CCNS présente une synthèse immédiate du contrôle salarial déjà réalisé sur le périmètre courant de l'audit des contrats. Il sert à repérer rapidement si les contrats affichés sont conformes, non conformes ou non évaluables sans ouvrir chaque fiche de détail.

## Indicateurs affichés

L'écran d'audit CCNS affiche les indicateurs suivants :

- nombre de contrats contrôlés ;
- nombre de contrats conformes ;
- nombre de contrats non conformes ;
- nombre de contrats non évaluables ;
- montant total des écarts salariaux ;
- pourcentage de contrats conformes ;
- pourcentage de contrats non conformes ;
- date de référence du contrôle.

Le montant total des écarts reste un `Decimal` dans le présentateur applicatif. La conversion en libellé monétaire n'intervient qu'à la frontière d'affichage.

## Calcul des pourcentages

Les pourcentages sont calculés avec `Decimal`, sans `float` :

- `% conformes = contrats conformes / contrats contrôlés * 100` ;
- `% non conformes = contrats non conformes / contrats contrôlés * 100`.

Les valeurs sont arrondies à deux décimales. Lorsque le périmètre ne contient aucun contrat salarial contrôlé, les deux pourcentages valent `0,00 %`.

## Périmètre

Le tableau de bord utilise exclusivement les `salary_control_row` déjà attachées aux lignes d'audit chargées. Les lignes sans contrôle salarial sont ignorées. Après application des filtres existants de l'audit, la synthèse est recalculée sur les lignes filtrées afin de rester cohérente avec la liste visible.

Les boutons **Voir les non conformes** et **Voir les non évaluables** pilotent uniquement le filtre salarial existant. Ils ne reconstruisent pas les données et ne déclenchent pas de nouvel audit.

## Absence de recalcul

Le tableau de bord ne lit aucun repository, n'accède pas à la base et n'appelle aucun contrôleur salarial. Il agrège uniquement les résultats déjà produits par l'audit courant.

## Limites connues

- Le tableau de bord ne conserve aucun historique : l'historisation relève d'une étape ultérieure de la roadmap.
- Les lignes dépourvues de `salary_control_row` ne sont pas comptées, car aucun résultat salarial exploitable n'est disponible pour elles.
- La date de référence affichée suppose que les lignes agrégées proviennent du même audit. Le présentateur refuse un mélange de dates différentes pour éviter une synthèse ambiguë.
