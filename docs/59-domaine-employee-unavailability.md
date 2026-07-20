# Domaine `EmployeeUnavailability`

`EmployeeUnavailability` représente une période datée et horaire pendant
laquelle un `Employee` est déclaré indisponible. Cette période est uniquement
déclarative : elle ne valide pas une demande de congé, ne contrôle pas le
planning et ne déclenche aucune règle CCNS, contractuelle ou de paie.

## Responsabilités

Une indisponibilité contient :

- un identifiant `UUID` ;
- le salarié `Employee` concerné ;
- une date et heure de début `starts_at` ;
- une date et heure de fin `ends_at` ;
- un motif `EmployeeUnavailabilityReason` ;
- un libellé optionnel ;
- des observations optionnelles ;
- un indicateur `active` explicitement déclaré.

L'objet est une dataclass immutable avec `slots`. Il appartient uniquement au
domaine métier et ne dépend d'aucune interface, persistance, API, bibliothèque
technique ou date système.

## Motifs déclaratifs

`EmployeeUnavailabilityReason` expose les valeurs `LEAVE`, `SICKNESS`,
`TRAINING`, `PERSONAL`, `PROFESSIONAL` et `OTHER`. L'énumération reste
strictement déclarative et ne produit aucune règle automatique de paie, de
contrat, de congé ou de temps de travail.

## Règles de validation

Le salarié est obligatoire et doit être une instance de `Employee`. Le motif est
obligatoire et doit être une instance de `EmployeeUnavailabilityReason`.

`starts_at` et `ends_at` sont obligatoires et doivent être des `datetime`. Les
objets `date` simples sont refusés explicitement. Les deux valeurs doivent être
soit toutes les deux naïves, soit toutes les deux dotées d'un fuseau horaire
compatible. Aucune conversion automatique de fuseau horaire n'est réalisée et les
objets `datetime` fournis ne sont pas modifiés.

La fin doit être strictement postérieure au début. Les durées nulles et les fins
antérieures sont refusées.

`label` et `observations` sont optionnels. Lorsqu'une valeur est fournie, les
espaces de début et de fin sont supprimés, puis une chaîne vide est refusée.

`active` doit être strictement booléen.

## Méthodes métier

- `duration()` retourne exactement `ends_at - starts_at`, sans arrondi.
- `is_active()` retourne uniquement la valeur déclarée de `active`, sans calcul à
  partir de la date courante.
- `has_label()` indique si un libellé est renseigné.
- `has_observations()` indique si des observations sont renseignées.
- `overlaps(starts_at, ends_at)` applique les intervalles semi-ouverts
  `[starts_at, ends_at[` avec la formule `self.starts_at < ends_at and starts_at
  < self.ends_at`. Deux périodes seulement adjacentes ne se chevauchent donc pas.
- `contains(moment)` retourne `True` pour `self.starts_at <= moment < self.ends_at`.

## Limites explicites

`EmployeeUnavailability` ne dépend pas de `MissionOccurrence`, de
`MissionOccurrenceAssignment` ou de `PlanningConflictService`. Le rapprochement
entre indisponibilités et affectations relève d'un futur service distinct.

L'objet ne modélise ni compteur de congés, ni arrêt de travail, ni justificatif,
ni maintien de salaire, ni indemnité, ni disponibilité récurrente, ni journée
entière implicite, ni suppression ou modification automatique d'affectation.
