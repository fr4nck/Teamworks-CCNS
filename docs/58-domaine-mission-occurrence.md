# Domaine `MissionOccurrence`

`MissionOccurrence` représente une occurrence concrète, datée et horaire, d'une
`Mission`. La mission reste la source de vérité pour la définition fonctionnelle
et ses exigences éventuelles ; l'occurrence ne porte que les informations propres
au créneau planifié.

## Responsabilités

Une occurrence contient :

- un identifiant `UUID` ;
- la `Mission` concernée ;
- une date et heure de début `starts_at` ;
- une date et heure de fin `ends_at` ;
- un lieu optionnel ;
- des observations optionnelles ;
- un indicateur `active` explicitement déclaré.

L'objet est une dataclass immutable avec `slots` et appartient uniquement au
domaine métier. Il ne dépend d'aucune interface, persistance, API ou bibliothèque
technique.

## Règles de validation

La mission est obligatoire et doit être une instance de `Mission`.

`starts_at` et `ends_at` sont obligatoires et doivent être des `datetime`. Les
objets `date` simples sont refusés explicitement. Les deux valeurs doivent être
cohérentes vis-à-vis du fuseau horaire : soit toutes les deux naïves, soit toutes
les deux dotées d'un fuseau horaire. Aucune conversion automatique n'est réalisée
et les objets `datetime` fournis ne sont pas modifiés.

La fin doit être strictement postérieure au début. Les durées nulles et les fins
antérieures sont donc refusées.

`location` et `observations` sont optionnelles. Lorsqu'une valeur est fournie,
les espaces de début et de fin sont supprimés, puis une chaîne vide est refusée.

`active` doit être strictement booléen.

## Méthodes métier

- `duration()` retourne exactement `ends_at - starts_at`, sans arrondi.
- `has_location()` indique si un lieu est renseigné.
- `is_active()` retourne uniquement la valeur déclarée de `active`, sans calcul à
  partir de la date courante.
- `occurs_on(day)` accepte une `date` simple, refuse explicitement un `datetime`,
  et indique si le jour civil de début de l'occurrence correspond à `day`, sans
  conversion de fuseau horaire.

## Limites explicites

`MissionOccurrence` ne représente pas l'affectation d'un salarié au créneau. Elle
ne contient ni contrôle de disponibilité, ni contrôle de contrat, ni contrôle de
qualification, ni décision d'éligibilité, ni récurrence, ni conflit de planning,
ni pause, ni temps de travail, ni rémunération.
