# Domaine `QualificationRequirement`

`QualificationRequirement` définit le besoin d'une `Qualification` dans un
contexte métier qui sera rattaché ultérieurement. C'est un objet domaine
immutable et pur : il n'a aucune dépendance vers la persistance, l'interface
graphique, le Web ou une API.

## Données portées

- identifiant UUID ;
- `Qualification` obligatoire ;
- niveau d'exigence (`RequirementLevel`) : requis, recommandé ou optionnel ;
- indicateurs booléens d'obligation et d'activité ;
- observations facultatives.

Le niveau doit appartenir à l'énumération dédiée. Les indicateurs doivent être
des booléens. Lorsqu'elles sont fournies, les observations sont normalisées par
suppression des espaces en début et fin de valeur ; une valeur vide ou d'un
autre type est refusée.

## Questions métier

- `is_required()` indique un niveau `REQUIRED` ;
- `is_recommended()` indique un niveau `RECOMMENDED` ;
- `is_optional()` indique un niveau `OPTIONAL`.

Ces méthodes décrivent uniquement le niveau déclaré ; elles ne réalisent aucun
contrôle automatique ni aucune comparaison avec une qualification détenue par
un salarié.

## Limites explicites

Cette définition ne porte aucune mission, poste, activité, salarié, contrat ou
planning. Elle ne contient aucune règle d'équivalence, passerelle, persistance
ou vérification automatique. Le rattachement futur de l'exigence à un contexte
métier relève d'un objet domaine distinct.
