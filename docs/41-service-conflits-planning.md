# Service de conflits directs de planning

`PlanningConflictService` détecte uniquement les chevauchements horaires directs entre affectations actives d'un même salarié à des occurrences actives de mission.

## Périmètre

Le service appartient au domaine pur. Il ne dépend pas de wxPython, d'une base de données, d'une API, du Web, de la persistance ni de la date courante. Il ne traite pas les règles CCNS, les qualifications, les temps de trajet, les pauses, les repos, les contrats, les indisponibilités ou une résolution automatique.

## Affectations retenues

Une affectation est évaluée seulement si elle concerne le salarié demandé, est active, référence une occurrence active et porte le statut `PLANNED` ou `CONFIRMED`. Les statuts `CANCELLED`, `COMPLETED` et `ABSENT` sont ignorés sans déduction automatique à partir des dates.

Les affectations répétées dans la collection d'entrée sont dédupliquées par UUID en conservant leur première position.

## Chevauchement

Les intervalles sont semi-ouverts : `[starts_at, ends_at[`. Deux occurrences sont en conflit lorsque `A.starts_at < B.ends_at` et `B.starts_at < A.ends_at`. Deux occurrences adjacentes ne sont donc pas conflictuelles.

Les datetime comparés doivent être tous naïfs ou tous avec fuseau horaire. Le service refuse explicitement le mélange et ne convertit pas les fuseaux horaires.
