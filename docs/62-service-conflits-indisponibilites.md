# Service de conflits entre affectations et indisponibilités

`UnavailabilityConflictService` est un service métier pur du domaine planning. Il détecte uniquement les chevauchements horaires directs entre les affectations à des occurrences de mission et les indisponibilités déclarées d'un même salarié.

## Périmètre

Le service ne dépend d'aucune interface graphique, persistance, API ou horloge système. Il ne modifie pas les affectations, les occurrences, les indisponibilités ou leurs statuts. Il ne porte aucune règle CCNS, de paie, de congé, de contrat, de qualification, de repos, de pause, de temps de trajet ou de notification.

## Entrées retenues

Une affectation est considérée seulement lorsqu'elle :

- concerne le salarié évalué, comparé par UUID ;
- est active ;
- référence une occurrence active ;
- possède le statut `PLANNED` ou `CONFIRMED`.

Les affectations `CANCELLED`, `COMPLETED` et `ABSENT` sont ignorées sans déduire de statut à partir des dates.

Une indisponibilité est considérée seulement lorsqu'elle :

- concerne le salarié évalué, comparé par UUID ;
- est active.

Tous les motifs d'indisponibilité sont traités de manière identique.

## Déduplication et ordre

Les affectations et indisponibilités sont dédupliquées par UUID avant filtrage métier. La première occurrence rencontrée est conservée et l'ordre d'entrée reste stable. Les conflits retournés suivent ensuite l'ordre naturel : ordre des affectations retenues, puis ordre des indisponibilités retenues.

## Définition du chevauchement

Les intervalles sont semi-ouverts : `[starts_at, ends_at[`. Un conflit existe lorsque :

```text
assignment.occurrence.starts_at < unavailability.ends_at
unavailability.starts_at < assignment.occurrence.ends_at
```

Des périodes seulement adjacentes ne produisent donc aucun conflit. Le chevauchement retourné est exactement :

```text
overlap_start = max(assignment.occurrence.starts_at, unavailability.starts_at)
overlap_end = min(assignment.occurrence.ends_at, unavailability.ends_at)
```

## Cohérence des dates et heures

Les dates et heures comparées doivent rester compatibles avec les règles existantes des indisponibilités : pas de mélange entre `datetime` naïfs et `datetime` avec fuseau, et pas de fuseaux différents. Le service refuse ces cas explicitement, sans conversion automatique et sans modifier les valeurs fournies.
