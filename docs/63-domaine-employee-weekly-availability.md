# Domaine EmployeeWeeklyAvailability

`EmployeeWeeklyAvailability` représente un créneau hebdomadaire déclaré pour un salarié.
Il modélise uniquement une disponibilité habituelle, par jour ISO de semaine, avec une
heure de début, une heure de fin et une période d'application optionnelle.

## Périmètre

Le domaine reste pur : aucune persistance, aucune interface graphique, aucune API et
aucune consultation de la date ou de l'heure courante. Le statut `active` est une
information déclarée et n'est jamais recalculé à partir des dates d'application.

## Règles principales

- `Weekday` expose les sept jours ISO, de `MONDAY = 1` à `SUNDAY = 7`.
- Les horaires doivent être deux objets `time`, soit tous deux naïfs, soit tous deux
  associés au même fuseau horaire.
- La fin doit être strictement postérieure au début ; les créneaux de durée nulle et
  les créneaux traversant minuit sont refusés.
- `effective_from` et `effective_until` sont optionnels et acceptent la même date.
- `applies_on(day)` vérifie le jour de semaine et les bornes de période, sans tenir
  compte de `active`.
- `contains(moment)` applique un intervalle semi-ouvert `[starts_at, ends_at[` et ne
  convertit jamais les fuseaux horaires.

## Limites volontaires

Ce modèle ne vérifie pas les affectations, les conflits, les indisponibilités, les
contrats, les règles CCNS, les règles de paie, les repos, les jours fériés, les pauses
ou les temps de trajet. Ces contrôles relèveront de services distincts.
