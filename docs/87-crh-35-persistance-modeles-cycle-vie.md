# CRH-35 — persistance des modèles de cycle de vie RH

## Objet

CRH-35 raccorde les modèles locaux introduits par CRH-34 à la base Teamworks active. Il persiste uniquement la **configuration explicite** de la structure ; il ne détecte encore aucun événement et ne crée aucune démarche.

## Schéma additif

Le composant versionné `hr_lifecycle_templates` ajoute :

- `tw_hr_lifecycle_templates` ;
- `tw_hr_lifecycle_template_documents`.

Il réutilise la table commune `tw_hr_schema_versions`, qu'il sait également créer lorsque ce composant est initialisé isolément.

Aucune table historique Teamworks n'est modifiée. Aucune clé étrangère n'est créée vers les personnes ou les contrats.

## Données persistées

Un modèle conserve :

- son identifiant local ;
- la nature d'événement générique ;
- le code organisme ;
- le code et le libellé du type de démarche interne ;
- le décalage d'échéance facultatif ;
- son état actif/inactif ;
- la liste ordonnée des pièces explicitement configurées avec leur caractère obligatoire/facultatif.

Aucun catalogue réglementaire, secret, jeton, donnée médicale ou document binaire n'est enregistré.

## Modification et désactivation

`save_template()` représente l'état courant de la configuration. Une modification remplace transactionnellement la projection du modèle et sa liste de pièces.

Le repository n'expose pas de suppression de modèle. Pour retirer une règle de la planification, elle est persistée avec `enabled=False`. CRH-34 ignore alors ce modèle sans perdre sa définition locale.

## Compatibilité de production

`TeamworksHrLifecycleTemplateRepository` utilise la frontière `GestionDB` déjà qualifiée afin de conserver les chemins :

- SQLite local ;
- MySQL/MariaDB réseau historique.

Le schéma n'utilise ni `ON CONFLICT`, ni `INSERT OR REPLACE`, ni `INSERT OR IGNORE`, ni `PRAGMA` dans l'adaptateur de production.

La lecture des pièces des modèles est groupée pour la liste d'un type d'événement et évite une requête par modèle.

## Runtime

`HrLifecyclePlanningRuntimeFactory` compose :

- l'identité stable de la structure active ;
- la persistance des modèles locaux ;
- les profils d'organismes déjà configurés ;
- `HrLifecyclePlanningService`.

La façade publique demande uniquement un `HrLifecycleEvent`. Elle ne transmet ni `structure_ref`, ni connexion DB, ni repository à l'appelant.

## Garde-fous

CRH-35 n'ajoute :

- aucune détection automatique d'embauche ou de fin de contrat ;
- aucune matérialisation automatique de suggestion ;
- aucune échéance légale par défaut ;
- aucune transmission externe ;
- aucun code wxPython ;
- aucune modification du statut technique d'échange.

## Suite

Le prochain lot peut ajouter la **configuration contrôlée** de ces modèles : service d'écriture + interface dédiée, toujours sans catalogue réglementaire prérempli. La détection des événements depuis les contrats Teamworks restera ensuite un lot distinct et auditable.
