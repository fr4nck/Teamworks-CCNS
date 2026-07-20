# Domaine `MissionAssignment`

`MissionAssignment` représente l'affectation métier générale d'un `Employee` à
une `Mission`. Cette affectation peut être bornée par une date de début et/ou
une date de fin, mais elle ne constitue pas une occurrence planifiée.

L'objet est immutable et appartient au domaine pur : il ne dépend ni de
wxPython, ni d'une base de données, ni de SQLAlchemy, ni d'une API, ni d'une
interface Web ou graphique, ni d'un module de persistance ou de planning.

## Données portées

- identifiant UUID ;
- salarié obligatoire de type `Employee` ;
- mission obligatoire de type `Mission` ;
- date de début facultative ;
- date de fin facultative ;
- indicateur d'activité strictement booléen ;
- observations facultatives, normalisées par suppression des espaces
  périphériques.

Les dates facultatives doivent être des objets `date`. Les objets `datetime`
sont explicitement refusés afin d'éviter d'introduire implicitement un horaire
ou un créneau de planning. Lorsque les deux dates sont renseignées, la date de
fin doit être supérieure ou égale à la date de début.

## Méthodes métier

- `has_start_date()` indique si une date de début est renseignée ;
- `has_end_date()` indique si une date de fin est renseignée ;
- `is_open_ended()` indique si aucune date de fin n'est renseignée ;
- `is_active()` retourne uniquement la valeur déclarée de l'indicateur
  `active`.

`is_active()` ne calcule jamais l'activité à partir de la date courante. Une
affectation terminée peut donc rester déclarée active, et une affectation sans
borne de fin peut rester déclarée inactive, selon la décision métier portée par
le champ `active`.

## Limites explicites

`MissionAssignment` ne porte ni horaire, ni heure de début ou de fin, ni lieu,
ni durée, ni récurrence, ni planning, ni occurrence de mission. Il ne vérifie
pas les qualifications détenues par le salarié, ne recopie pas les exigences de
qualification de la mission, ne prend aucune décision d'éligibilité, ne crée
pas de contrat automatique et n'introduit pas de poste.
