# Domaine `Qualification`

`Qualification` définit une qualification disponible dans le référentiel de
l'association : compétence, diplôme, certification, habilitation, autorisation
ou permis. C'est un objet domaine immutable, sans dépendance vers une couche
technique, l'interface graphique ou la persistance.

## Données portées

- identifiant UUID ;
- code et nom obligatoires ;
- catégorie (`QualificationCategory`) : diplôme, certification, autorisation,
  formation, permis ou autre ;
- durée de validité facultative, exprimée en jours ;
- indicateurs de renouvellement, d'obligation et d'activité.

Les textes obligatoires sont normalisés par suppression des espaces en début et
fin de valeur. La catégorie doit appartenir à l'énumération dédiée, la durée
de validité doit être un entier positif ou nul lorsqu'elle est fournie, et les
trois indicateurs doivent être des booléens.

## Questions métier

- `is_permanent()` indique l'absence de durée de validité ;
- `requires_renewal()` indique si la qualification est renouvelable ;
- `has_expiration()` indique la présence d'une durée de validité.

Ces méthodes ne calculent aucune date : elles caractérisent uniquement la
définition de la qualification.

## Limites explicites

`Qualification` ne représente pas la possession d'une qualification par un
salarié. Il ne porte donc ni `Employee`, ni contrat, date d'obtention ou
d'expiration, historique, organisme formateur, justificatif, document ou
contrôle réglementaire. Ces informations relèveront d'une relation métier
dédiée entre un salarié et une qualification.
