# Teamworks-CCNS — suivi CCNS et extensions

**Mise à jour : 4 septembre 2026**

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

## Rapports de crash

Le dialogue de crash peut envoyer, après confirmation explicite, le seul rapport
technique `.txt` au destinataire partagé défini dans **Préférences → Maintenance /
Diagnostic**. Ce réglage est stocké dans la base sous `maintenance /
adresse_rapport_bugs`. Si le champ est vide ou absent, Teamworks conserve le
comportement historique et utilise `noethys@gmail.com`, l'adresse d'origine d'Ivan.
L'envoi utilise l'adresse expéditeur par défaut déjà configurée dans Teamworks ; en
son absence, aucun envoi n'a lieu et le fichier reste disponible dans `Logs`.

## Interopération — réalisé validé vers le domaine RH

Teamworks peut recevoir le contrat transverse `session-actual/1`, événement
`session_actual_validated`, provenant du domaine stable `operations_portal`.
Cette entrée est volontairement séparée du planning prévisionnel et de la paie.

Le lot RH ajoute :

- un mapping explicite `person_uid` stable → `personnes.IDpersonne` existante ;
- aucune création automatique de salarié lorsqu'un UID reçu est inconnu ;
- une inbox idempotente et un journal RH courant du réalisé par `session_uid` ;
- refus des révisions obsolètes et des payloads divergents ;
- garde de concurrence empêchant une ancienne révision d'écraser une plus récente ;
- réception de l'enveloppe authentifiée `inter-domain-delivery/1` avec HMAC-SHA256 et rotation par `key_id` ;
- client sortant `inter-domain-mailbox-pull/1` en HTTPS, limité au domaine `hr_employment` ;
- redirections HTTP interdites afin de ne jamais retransmettre le bearer vers un autre origin ;
- acquittement terminal des messages déterministement invalides pour éviter les boucles de poison message ;
- aucune écriture directe dans les contrats, le planning prévisionnel ou la paie.

Le bearer de transport et la clé HMAC de l'enveloppe restent des secrets distincts.
Le transport HTTP est isolé de l'orchestration métier afin de pouvoir être remplacé
ultérieurement par une queue ou un broker sans modifier le consommateur RH.

## Teamworks Qt — sécurité des données (RC2)

Défauts propres à l'application Qt du fork, confirmés à l'audit des chemins
d'ouverture et d'écriture, puis corrigés :

- **modification concurrente d'un contrat** : l'enregistrement relisait la base
  au moment de la sauvegarde, si bien qu'une modification faite entre-temps par
  une autre session (autre poste, Teamworks wx) était écrasée sans avertissement.
  La ligne est désormais relue sous verrou d'écriture (`BEGIN IMMEDIATE` sous
  SQLite, `SELECT … FOR UPDATE` sous MySQL) et comparée à l'état affiché à
  l'ouverture ; toute différence refuse l'enregistrement (`CONFLICT`) ;
- **relecture après commit non comparée** : le contrat relu est maintenant comparé
  champ par champ aux valeurs saisies ; un écart est signalé comme
  « enregistré · vérification en échec » et jamais comme un succès ;
- **lecture SQL en échec présentée comme vide** : `GestionDB.ExecuterReq` avale
  l'erreur et renvoie 0 ; les lecteurs Personnes, Contrats et Activité lèvent
  désormais une erreur explicite, et une lecture ratée vide la liste des contrats
  au lieu de laisser ceux de la fiche précédente. Le comportement d'origine de
  `ExecuterReq` est un candidat Vanilla **non vérifié** dans `Noethys/Teamworks` ;
- **base active non affichée** : la base réellement ouverte (fichier SQLite ou
  serveur MySQL, sans mot de passe) est affichée en permanence dans la barre
  d'état (nom accessible complet, lu par les lecteurs d'écran) et le titre ;
  sans base sélectionnée dans `Config.json`, Qt refuse de
  démarrer sans rien ouvrir ;
- **sauvegardes SQLite** : nom réservé en création exclusive (deux sauvegardes au
  même instant ne partagent jamais un fichier) et contrôle du contenu table par
  table ; nouvelle restauration isolée qui refuse la base active, une destination
  existante et une sauvegarde corrompue.

Le gate MySQL synthétique de la CI (MySQL 8.0, schéma historique) a révélé que le
contrôle du moteur de stockage passait par `GestionDB.ExecuterReq`, qui réécrit
tout `()` pour MySQL et rendait `DATABASE()` invalide : toute base MySQL aurait été
refusée. La requête passe désormais par le curseur, et le faux MySQL des tests
reproduit cette réécriture.

Le gate MySQL/MariaDB sur copie représentative reste **BLOCKED** : aucun serveur ni copie représentative
autorisée n'est disponible sur le poste de recette.

### Connexion MySQL de l'exe Qt Windows

- **défaut d'empaquetage** : PyInstaller n'embarquait pas les modules chargés
  dynamiquement par `mysql.connector` (traductions des erreurs client, plugins
  d'authentification). Toute erreur côté client devenait
  `ImportError: No localization support for language 'eng'`, et un compte
  `mysql_native_password` (MySQL 5.7) n'avait pas de plugin. Ces modules sont
  désormais embarqués (`d3134cf`) ; l'inventaire de l'archive du binaire le
  confirme, seuls `aio` et `django`, inutilisés, en sont absents ;
- **diagnostic en lecture seule** : `Teamworks-CCNS-Qt.exe --diagnostic-mysql`
  distingue l'accès TCP, la négociation MySQL (version du serveur, méthode
  d'authentification annoncée), l'authentification, la sélection de la base et
  la compatibilité du schéma. Il n'exécute que `USE`, `SELECT` et `SHOW` et
  écrit un rapport neuf `diagnostic-mysql-*.txt` à côté de `Config.json`, sans
  jeton ni mot de passe. Code 0 si les cinq étapes passent, 6 sinon ;
- **compatibilité historique** : le pilote est figé à
  `mysql-connector-python==9.7.0`. Le packaging teste le binaire réel contre
  MySQL 5.7.31 sous Windows : diagnostic complet, démarrage en production,
  mot de passe refusé (1045), port fermé et base inaccessible. Le job CI
  `mysql-historique` exécute le parcours contrats et le diagnostic contre
  MySQL 5.7.31 (bloquant), ainsi que contre 5.5.62 et avec le connecteur 26.7.0
  de wx rc8 (à titre d'information) ;
- **écart avec wx** : Qt lit le même `Config.json` que wx (hors mode Portable),
  avec les mêmes options de connexion (`UTILS_MySQL` : Python pur, `utf8`, TLS
  seulement si des certificats sont configurés). En revanche, wx rc8 embarque
  `mysql-connector-python` 26.7.0, et Qt ignore `interface_mysql`, car MySQLdb
  n'est pas embarqué. La connexion au serveur de production n'est pas vérifiée
  depuis le poste de développement.

## Références principales

- `ROADMAP.md`
- `docs/48-revue-architecture-ccns.md`
- `docs/50-scope-metier.md`
- `docs/60-scenario-utilisation-controle-salarial.md`
- documentation `docs/40-*` à `docs/65-*`
