# Architecture cible de Teamworks-CCNS

## Portée de ce document

Ce document décrit uniquement les décisions propres à **Teamworks-CCNS**.

Les décisions transverses entre applications, Portail, hébergement et infrastructure relèvent de **`fr4nck/PMSL-Arch`** et de ses ADR acceptées. Elles ne doivent pas être redéfinies ici.

## Décision retenue

- **Teamworks-CCNS** = cœur métier RH principal ;
- **Qt / PySide6** = interface desktop cible ;
- trois branches permanentes sont maintenues : **`master`**, **`wx/master`** et **`qt/master`**.

## Rails de développement

### `wx/master`

`wx/master` est le rail wxPython / production et la référence métier historique pendant la transition.

Il reçoit :
- corrections métier communes ;
- conformité CCNS, réglementaire et sociale ;
- sécurité ;
- compatibilité avec les environnements de production ;
- corrections fonctionnelles ;
- corrections UI wxPython nécessaires à la stabilité, au rendu, au layout, au thème ou au zoom ;
- adaptations limitées nécessaires à une migration Qt propre.

Il n'a plus vocation à recevoir de grandes refontes d'interface destinées à être remplacées par Qt.

### `qt/master`

`qt/master` est le rail principal de migration Qt.

Il reçoit :
- nouveaux développements UI structurants ;
- migration progressive des écrans et domaines ;
- composants Qt et leurs tests spécifiques ;
- synchronisations contrôlées des changements métier communs qualifiés sur `master`.

Le rail Qt ne doit pas dupliquer du SQL ou des règles métier qui peuvent être partagés avec le cœur commun.

### `master`

`master` porte les domaines, services, infrastructures, outils, documentation et CI transversaux.

### Synchronisation

Les changements communs sont intégrés et qualifiés sur `master`, puis portés explicitement vers les rails concernés. Un correctif découvert sur wx ou Qt peut être extrait vers le socle partagé.

Les transferts restent ciblés et qualifiés : aucun merge massif entre rails, aucune synchronisation automatique.

Les seules branches de travail autorisées sont `master`, `wx/master` et `qt/master`. Ne pas créer de branche temporaire. Les anciennes branches sont supprimées après conservation de leur contenu utile ou décision explicite d'abandon.

## Rôle du cœur Teamworks

Le cœur Teamworks doit porter :
- gestion des personnes ;
- profils juridiques ;
- contrats ;
- régimes d'emploi ;
- classifications ;
- grilles salariales ;
- règles de calcul ;
- anomalies ;
- habilitations ;
- historique sensible ;
- écrans de contrôle.

## Transition wxPython vers Qt

**Le rail wx reste la référence métier historique pendant la migration vers Qt.**

- wxPython est stabilisé : il n'a plus vocation à recevoir de grandes refontes d'interface.
- Les nouveaux développements UI structurants ont vocation à être réalisés en Qt.
- La migration est progressive, écran par écran et domaine par domaine.
- Qt ne doit pas embarquer directement du SQL ou des règles métier qui peuvent être séparées de l'interface.
- Le comportement wxPython historique n'est pas automatiquement normatif : un bug identifié doit être corrigé ou explicitement arbitré avant d'être reproduit en Qt.

Le gel des refontes wxPython **n'interdit pas les corrections**. Restent autorisés :
- bugs fonctionnels ;
- bugs graphiques, de layout, de thème, de zoom ou de rendu ;
- régressions ;
- corrections de règles métier erronées ;
- conformité CCNS, réglementaire ou sociale ;
- sécurité ;
- compatibilité avec les environnements de production ;
- adaptations limitées nécessaires à une migration Qt propre.

Principe : **on corrige ce qui dysfonctionne dans wxPython, mais on évite d'y investir dans une nouvelle refonte UI destinée à être remplacée par Qt.**

## Historique de qualification Qt

La PR **#366** a qualifié le POC Qt initial sur Linux et Windows. Son HEAD qualifié a servi de point de départ au rail durable **`qt/master`**.

Les PR techniques **#377**, **#378** et **#380** ont été convergées par **#381**, puis fermées comme superseded. La PR #366 a ensuite été fermée sans merge vers la branche historique `master` : elle reste une archive de qualification, pas le mécanisme de développement courant du rail Qt.

## Frontière moteur / carrosserie : premier lot sans wx

Le moteur partagé est constitué de `domain/`, `application/` et `infrastructure/`.
Il ne doit importer ni wxPython ni PySide6. Les widgets et les événements
restent dans les carrosseries (`wx/master` pour l'historique et `qt/master` pour Qt).

La sélection de la base active est désormais isolée dans
`infrastructure/persistence/current_database_config.py`, qui lit uniquement
le `nomFichier` du `Config.json` historique, sans créer ni modifier de fichier
et sans interface graphique. Les noms de bases locaux et les références
réseau historiques sont conservés tels quels.

Dans la carrosserie Qt, `GestionDB` et `UTILS_Fichiers` doivent consommer
la configuration par cette frontière et par un lecteur INI sans wx.
Cette étape ne modifie pas le comportement de l'application historique
sur `wx/master`; l'extraction progressive du reste de `GestionDB` est à
qualifier indépendamment avant de supprimer l'adaptateur legacy.

Le maintien de la compatibilité SQLite/MySQL, la fermeture des connexions,
les transactions et la recette Windows sur copie réelle restent des gates
distincts. Une CI verte ne constitue pas une recette terrain.

## Connexion MySQL historique : frontière sans UI

Le module infrastructure/persistence/legacy_network_target.py decode le format
port;hote;utilisateur;jeton[RESEAU]base sans acces a wx, Qt ou a la base.
Il conserve les alias des parametres historiques, l'abaissement du nom de
base et le jeton opaque de mot de passe (y compris #64#). Il masque
le secret dans sa representation et n'inclut pas la reference brute dans
ses erreurs de validation.

Ce composant ne connecte pas MySQL : le choix du pilote, le decodeur de jeton
et les operations SQL restent provisoirement dans l'adaptateur legacy. Les
tests unitaires couvrent le format, les erreurs et l'absence de dependance UI.
La recette serveur MySQL/MariaDB reel et la verification des versions historiques
restent obligatoires avant toute qualification de production.

## SQLite legacy : ouverture et cycle de vie sans interface

L'ouverture de fichiers SQLite historiques est extraite dans
`infrastructure/persistence/legacy_sqlite_connection.py`, sans aucun import
wxPython ni Qt. Le mode lecture refuse de creer un fichier absent ; la creation
reste explicite. Les parametres sqlite3 restent ceux de l'application historique.
En cas d'echec de creation de curseur, la connexion ouverte est refermee.

`infrastructure/persistence/legacy_connection_lifecycle.py` fournit des
primitives de commit et fermeture, communes aux connexions SQLite/MySQL,
sans imposer un commit ou un rollback implicite. Les diagnostics, l'identite
des connexions, la gestion d'erreurs et les frontieres transactionnelles
restent pilotes par l'adaptateur appelant.

Le raccordement cible est exclusif a `qt/master`. `wx/master` n'est pas
modifiee. Le module `GestionDB` conserve provisoirement le code historique
des photos, imports/exports SQLite, les drivers MySQL et les transactions SQL
specialisees. Les tests du module ne remplacent pas la recette Windows/DB reelle.

## Ouverture MySQL independante de la carrosserie

La fonction `infrastructure.persistence.legacy_mysql_connection.open_legacy_mysql`
ouvre une connexion pour un `LegacyNetworkTarget` deja qualifie,
sans charger wxPython, PySide6, mysql.connector, MySQLdb ou GestionDB.
Les pilotes, decodeurs de mots de passe historiques, options SSL et formats
de diagnostics lui sont injectes par l'adaptateur applicatif.

Le chemin mysql.connector conserve le mode Python pur et les parametres
compatibles MySQL/MariaDB historiques, via l'usine d'options existante.
Le chemin MySQLdb conserve la conversion LONG et le jeu de caracteres utf8.
Une erreur d'initialisation du jeu de caracteres libere la connexion ouverte.
Le module ne cree pas de base, ne selectionne pas de schema et ne fait
aucun commit/rollback implicite.

La qualification de ce moteur ne constitue pas une validation de la
base de production. Le raccordement a GestionDB est exclusivement
effectue sur qt/master ; wx/master reste intacte.

## Selection MySQL et batches transactionnels

`infrastructure/persistence/legacy_mysql_schema.py` prepare et execute
l'activation des bases MySQL sans wx, Qt ni driver explicite. La creation
n'est executee que si demandee. Les noms de schema sont quotes comme
identifiants MySQL, avec verification des caracteres interdits avant SQL.
Les options historiques `utf8` / `utf8_unicode_ci` sont preservees.
La valeur sentinelle `_tdata` et les noms vides ne declenchent pas USE
lors d'une connexion ordinaire.

`infrastructure/persistence/legacy_sql_batch.py` centralise l'adaptation
historique des marqueurs SQLite/MySQL pour `executemany`, avec commit
explicite par defaut et aucune annulation automatique : la decision de
rollback appartient toujours au service appelant. Ces primitives ne
remplacent pas les services transactionnels metier deja existants.

Le raccordement des deux composants au `GestionDB` Qt est cible, qualifie
par tests unitaires, SQL SQLite reel et parcours Windows/MySQL de CI.
`wx/master` reste inchangee. Les cas de bases historiques non conformes
a la validation des identifiants doivent etre examines avant recette reelle.

## Trajectoire PostgreSQL (renvoi a PMSL-Arch ADR-010)

La decision transverse reste PMSL-Arch, ADR-010 (acceptee le 2026-08-29).
Il ne faut pas la redefinir dans le depot Teamworks.

- Portail (`fr4nck/Portails`) : PostgreSQL 18 est une cible candidate
  qualifiee en CI ; aucune bascule en production n'en decoule automatiquement.
- Teamworks : conserve aujourd'hui son fonctionnement SQLite et MySQL/MariaDB.
  Toute adoption de PostgreSQL vient **apres** la recette representatrice
  de Portail et doit faire l'objet d'un lot de migration propre a Teamworks.
- Noethys : conservation du socle MySQL 5.7 pendant la transition, sans
  imposer a Portail ou Teamworks une migration simultanee.

Les extractions actuelles dans `infrastructure/persistence/` sont des
adaptateurs aux moteurs historiques, pas une decision implicite de garder
MySQL pour toujours. Le domaine et les services metier doivent rester
independants du SQL, des transactions techniques, de wx et de Qt.

Les conditions de la future migration Teamworks incluent un inventaire
du schema et des dialectes, des migrations reversibles, une copie anonymisee
representative, tests RH/CCNS/CEE/ETP, contrats d'echange avec Portail,
verification des imports/exports et un retour arriere valide. Aucune
migration automatique de production ou ajout de pilote PostgreSQL dans
l'application Qt n'est autorise dans le lot de decouplage en cours.

## SQL de transfert des tables : compilation hors interface

Le fichier `infrastructure/persistence/legacy_table_transfer.py` prepare
les projections de colonnes et les requetes de copie historiques SQLite/MySQL.
Il ne charge ni wx/Qt, ni pilote de base, et n'ouvre pas de connexion.
Le moteur conserve l'ordre des colonnes de la source et les marqueurs
de parametres `?` (SQLite) et `%s` (MySQL). Le catalogue de tables
declarees dans `teamworks/Data/DATA_Tables.py` est teste : les identifiants
doivent etre compatibles avec une construction SQL non quotee.

Ce composant isole le dialecte legacy sans prejuger du futur dialecte
PostgreSQL. Il ne modifie ni le schema, ni les donnees, ni les transactions.
Son raccordement a GestionDB est reserve a `qt/master` avec tests de
non-regression ; `wx/master` reste intacte. L'inventaire des bases reelles
et la recette applicative demeurent necessaires avant la future migration.

## DDL historique et suppression SQLite reversible

Le composant `legacy_table_ddl.py` construit le DDL des tables de
`GestionDB` sans wx, Qt ou pilote SQL. Il conserve les adaptations de types
SQLite/MySQL du catalogue `Data/DATA_Tables.py`, notamment les seuils
VARCHAR, et valide les identifiants et types avant toute execution.
Les commandes ALTER et INDEX conservent leurs types historiques tels quels.

`legacy_sqlite_column_migration.py` supprime une colonne par `ALTER TABLE
DROP COLUMN` natif sous SQLite 3.35+ et SAVEPOINT. Aucun fallback destructeur
n'est autorise sur les versions plus anciennes. En cas
d'exception, ROLLBACK TO restaure la table et ses lignes ; en cas de
succes, RELEASE n'engage pas de commit de la transaction englobante.
Les tests couvrent l'echec injecte, le rollback explicite du code appelant,
la preservation des index et triggers non dependants, des vues, des cles
etrangeres et des contraintes, ainsi que l'echec sans modification du schema
si la colonne est encore utilisee. Le moteur SQLite refuse les suppressions
ambiguës plutot que de reconstruire silencieusement la table. Cette garantie
ne s'applique PAS a MySQL : son DDL peut provoquer un commit implicite.
Le RELEASE d'un SAVEPOINT exterieur est un commit ; au sein d'une transaction
englobante, il ne valide pas cette transaction.

`ReparationTable` et les conversions completes de bases demeurent hors
de ce lot compte tenu des risques d'integrite des donnees.
La version wx sur `wx/master` ne recoit aucune modification.

### Limites de schema avant migration de ReparationTable

`ReparationTable` utilise toujours une reconstruction historique destructive.
Elle n'a PAS ete migree par ce lot. Elle doit etre requalifiee en preserve-
schema avec les index, triggers, contraintes, vues et cles etrangeres reels.
Toute intervention sur une copie d'exploitation necessite backup et comparaison
schema + donnees avant/apres ; les tests unitaires n'en tiennent pas lieu.
