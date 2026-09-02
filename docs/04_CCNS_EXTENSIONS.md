# Teamworks-CCNS — suivi CCNS et extensions

**Mise à jour : 2 septembre 2026**

## Objectif

Ce fichier suit les **fonctionnalités ajoutées par notre fork** : règles CCNS, contrôles métier, nouveaux services, tableaux de bord, exports et extensions propres au produit.

## Règle de classement

- bug déjà présent dans Teamworks original → `01_VANILLA_BUGFIX.md` ;
- adaptation imposée par Python 3/Phoenix → `02_PYTHON3_PHOENIX.md` ;
- régression purement graphique → `03_UI_UX_MODERNISATION.md` ;
- comportement inexistant dans l'original et ajouté par notre fork → ce fichier.

## Méthode de mesure

Le chantier est découpé en **9 jalons fonctionnels de poids égal**. `Terminé` vaut 1 point, `Partiel` vaut 0,5 point et `À valider` vaut 0.

| Jalon | État | Situation actuelle |
|---|---|---|
| 1. Domaine et règles CCNS | Terminé | entités, classifications, grilles, minima et contrôles métier isolés et testés |
| 2. Schéma additif et accès aux données réelles | Terminé | schéma compatible historique, `CcnsDataReader`, `PersonReader`, raccords `GestionDB` |
| 3. Création et lecture des contrats CCNS modernes | Terminé au niveau automatisé | chemins dédiés, préflights et règles de création intégrés |
| 4. Contrats CEE | Terminé au niveau automatisé | chemin CEE et contrôles dédiés intégrés |
| 5. Opérations de contrats | Terminé au niveau automatisé | renouvellement CDD, transformation CDD→CDI et période d'essai couverts |
| 6. Contrôle salarial / minima / synthèses | Terminé au niveau automatisé | audit transverse, détail, synthèse individuelle et contrôles de rémunération |
| 7. Historique, alertes, exports et publipostage | Terminé au niveau automatisé | snapshots/rapports, CSV/JSON, modèles et publipostage raccordés |
| 8. Architecture d'intégration et versionnement réglementaire | Partiel | readers et adaptateurs réels présents ; date de référence injectable, persistance des versions de grille et certaines frontières restent à consolider |
| 9. Recette métier réelle sur copie PMSL | À valider | le parcours complet, notamment création réelle de contrats, doit encore être validé sur le portable exact de `master` |

## Avancement

7 jalons terminés + 1 jalon partiel sur 9 :

**CCNS & extensions : 7,5 / 9 = 83,3 %, arrondi à 83 %.**

Ce pourcentage mesure le développement fonctionnel et son intégration automatisée. Il ne remplace pas la recette utilisateur : une fonction couverte par tests n'est pas déclarée prête en production tant que le parcours réel n'a pas été validé sur une copie de base.

## Restant prioritaire

- produire et lancer le portable Windows du `master` exact ;
- créer/modifier réellement des contrats CCNS et CEE sur une copie de base ;
- vérifier renouvellement CDD et transformation CDD→CDI lorsque les données le permettent ;
- valider contrôle salarial, synthèses, historique et exports avec des données réelles ;
- injecter explicitement une date de référence dans l'audit avant d'activer davantage de logique réglementaire datée ;
- stabiliser la lecture persistée des versions de grille seulement dans un lot dédié et testé ;
- conserver la veille réglementaire descriptive tant qu'une validation métier/juridique n'a pas autorisé son activation automatique.

## Interopérabilité — réalisé validé des séances

Le domaine `hr_employment` dispose désormais d'un consommateur du contrat
`session-actual/1`, émis par le domaine stable `operations_portal` avec le type
d'événement `session_actual_validated`.

Principes du lot :

- inbox idempotente avec empreinte SHA-256, clé d'idempotence et unicité
  domaine + séance + révision ;
- journal RH additif du réalisé, distinct du planning prévisionnel, des contrats
  et de la paie ;
- résolution de `actual_staff_uid` par un mapping explicite vers une
  `IDpersonne` Teamworks existante ;
- aucun salarié n'est créé implicitement lorsqu'un UID RH est inconnu ;
- une séance annulée reste traçable mais ne porte ni intervenant, ni lieu, ni
  horaires ni durée réels ;
- une révision plus récente peut corriger le journal ; une révision obsolète ou
  divergente est refusée ;
- l'identité `actual_uuid` d'un réalisé ne peut pas changer pour une même
  `session_uid` ;
- les écritures du journal et de l'inbox sont atomiques ;
- aucun effet direct sur la production de bulletins de paie.

Le transport réseau reste un adaptateur séparé : ce consommateur constitue le
point d'entrée métier/persistance et ne lie pas Teamworks à un nom de produit ou
à une API HTTP particulière.

## Rapports de crash

Le dialogue de crash peut envoyer, après confirmation explicite, le seul rapport
technique `.txt` au destinataire partagé défini dans **Préférences → Maintenance /
Diagnostic**. Ce réglage est stocké dans la base sous `maintenance /
adresse_rapport_bugs`. Si le champ est vide ou absent, Teamworks conserve le
comportement historique et utilise `noethys@gmail.com`, l'adresse d'origine d'Ivan.
L'envoi utilise l'adresse expéditeur par défaut déjà configurée dans Teamworks ; en
son absence, aucun envoi n'a lieu et le fichier reste disponible dans `Logs`.

## Références principales

- `ROADMAP.md`
- `docs/48-revue-architecture-ccns.md`
- `docs/50-scope-metier.md`
- `docs/60-scenario-utilisation-controle-salarial.md`
- documentation `docs/40-*` à `docs/65-*`
