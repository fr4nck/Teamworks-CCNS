# Domaine `Employee`

`Employee` représente exclusivement l'identité métier d'un salarié de
l'association. C'est un objet domaine immutable et indépendant de toute couche
technique, de l'interface graphique, de la persistance et de la logique RH.

## Données portées

- identifiant UUID ;
- civilité (`Civility`) ;
- prénom et nom ;
- date de naissance facultative ;
- email professionnel facultatif ;
- téléphone professionnel facultatif ;
- indicateur d'activité.

Les prénom et nom sont obligatoires. L'identifiant doit être un UUID, la
civilité doit appartenir à l'énumération dédiée, la date de naissance ne peut
pas être future et l'email professionnel fourni doit avoir une forme valide.

## Limites explicites

`Employee` ne représente ni un compte utilisateur ni un contrat de travail. Il
ne porte donc aucune relation vers `Account` ou `Contract`, ni aucune donnée de
contrat, rémunération, temps de travail, planning, qualification, site,
activité ou rôle. Ces relations et concepts pourront être introduits par des
objets métier dédiés ultérieurement.
