# TW-185 — France Travail et recrutement

## Objectif

Moderniser le module historique de saisie des offres d'emploi sans casser les données existantes, puis permettre à terme de récupérer une offre France Travail depuis sa référence afin d'éviter les doubles saisies.

## Compatibilité historique

La base historique Teamworks stocke la référence externe dans la colonne `emplois.reference_anpe`.

Cette colonne **n'est pas renommée ni supprimée** : elle reste la clé de stockage historique pour préserver les bases existantes et la compatibilité MySQL/MariaDB 5.5.

Seule la présentation utilisateur évolue :

- `N° ANPE` → `Réf. France Travail` ;
- les infobulles ne doivent plus mentionner l'ANPE ;
- un diffuseur historique nommé `Pôle Emploi` ou `ANPE` peut être présenté comme `France Travail` sans modifier son identifiant ni les offres déjà enregistrées.

## Import d'une offre par référence

Parcours cible :

1. l'utilisateur saisit une référence France Travail, par exemple `210DQGB` ;
2. il clique sur `Importer` ;
3. Teamworks interroge l'intégration officielle France Travail lorsqu'elle est configurée ;
4. une prévisualisation affiche les données reçues et ce qui sera remplacé ;
5. l'utilisateur confirme explicitement l'application des données ;
6. l'offre reste ensuite modifiable normalement dans Teamworks.

L'import ne doit jamais écraser silencieusement une offre déjà renseignée.

## Données candidates à l'import

Selon les données effectivement fournies par l'API officielle et après mapping explicite :

- référence de l'offre ;
- intitulé ;
- descriptif ;
- type de contrat ;
- durée / temps de travail ;
- lieu de travail ;
- date de publication / actualisation ;
- informations de rémunération lorsqu'elles sont publiées ;
- informations employeur lorsqu'elles sont publiées.

Les `fonctions` et `affectations` internes Teamworks ne doivent pas être créées ou remplacées automatiquement à partir de texte libre. Un rapprochement pourra être proposé séparément.

## Architecture

L'écran wx ne doit pas contenir directement le protocole HTTP ni les secrets d'accès.

Prévoir :

- un client France Travail isolé dans l'infrastructure ;
- un service d'application transformant la réponse externe en proposition d'import ;
- un modèle de données indépendant de wx ;
- un dialogue de prévisualisation / confirmation ;
- des erreurs explicites en cas d'offre inconnue, API indisponible ou accès non configuré ;
- aucune dépendance réseau pour créer ou modifier manuellement une offre.

## Authentification et configuration

Les paramètres exacts d'authentification et les endpoints doivent provenir de la documentation officielle France Travail en vigueur au moment de l'implémentation.

Aucun secret ne doit être committé dans le dépôt ni codé en dur. L'absence de configuration France Travail doit simplement désactiver l'import automatique, sans bloquer le module recrutement.

## Critères de sortie du premier incrément

- vocabulaire `ANPE` / `Pôle Emploi` retiré de l'interface principale de saisie d'offre ;
- stockage historique `reference_anpe` conservé ;
- documentation du futur import par référence ;
- aucun changement destructif de schéma ;
- tests de non-régression sur la lecture et l'enregistrement d'une référence existante.
