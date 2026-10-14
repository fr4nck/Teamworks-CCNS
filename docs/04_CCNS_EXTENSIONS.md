# Teamworks-CCNS — suivi CCNS et extensions

**Mise à jour : 14 octobre 2026**

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

### Conservation et qualification du lot historique — 12 octobre 2026

Le sommet `3dadf2d0adc338bf2b5b45fcb49461d5bcfa37b1` de
`ccns/session-actual-hr-inbox` est conservé intégralement dans le tag annoté
`archive/2026-10-12/three-rails/ccns/session-actual-hr-inbox`, publié et vérifié.
Le domaine, les deux services, le repository, les exports et les trois migrations
SQL sont déjà présents sur les rails courants. Les huit fichiers de production
concernés sont identiques entre `master` et `wx/master` au constat du lot ;
les trois migrations et les exports sont identiques au sommet historique.
Les implémentations métier ont évolué, notamment pour distinguer les erreurs
techniques réessayables des refus déterministes et valider strictement les nombres.
La documentation conserve le mapping explicite, l'identité immuable du réalisé,
l'atomicité journal/inbox et l'interdiction de toucher contrats, planning et paie.

Les deux fichiers de tests historiques sont désormais repris sur `wx/master`.
Seul le motif d'erreur du test concurrent est adapté de « concurrente » à
« concurr », pour accepter le libellé actuel « modifiée concurremment » ;
les assertions de révision conservée et de nombre d'écritures restent intactes.
Avec les tests courants et le client mailbox, **48 tests passent** sous Windows,
Python 3.11, avec SQLite en mémoire et transports doublés. La compilation et
`git diff --check` passent. Aucune base réelle, recette réseau MySQL, application
graphique ou nouvelle CI Linux n'a été utilisée pour cette qualification.
Cette preuve porte sur la reprise des corrections et contrats automatisés du
lot historique, pas sur une qualification de production du transport RH.

## Références principales

- `ROADMAP.md`
- `docs/48-revue-architecture-ccns.md`
- `docs/50-scope-metier.md`
- `docs/60-scenario-utilisation-controle-salarial.md`
- documentation `docs/40-*` à `docs/65-*`


## Conservation CRH sur les rails permanents


Portage ciblé du socle partagé sur master et du raccord salarié sur wx/master, sans merge massif ni publication distante. La régression des champs résultat/commentaire de CRH-36 est reproduite sur MySQL 5.5.62 et MariaDB 10.11.14 : erreur 1406 en mode strict, troncature en mode permissif. La migration du composant `hr_cases_runtime` vers la version 2 élargit les champs sans réduire les données, contrôle les schémas connus et le moteur transactionnel, normalise les index et sérialise l'initialisation.

La configuration conserve les capacités existantes ; un nouveau profil reçoit uniquement les capacités manuelles du connecteur de référence disponible. OTHER reste configurable sans connecteur ni capacités annoncées.

Le raccord salarié réemploie le dialogue CRH-36 et invalide le runtime d'actions avant le rechargement. Les collisions concurrentes d'événements/créations sont converties en erreurs métier avec rollback. Le `save_case` générique conserve sa limite historique de dernière écriture gagnante ; les actions métier doivent utiliser les adaptateurs transactionnels dédiés.

Qualification et limites : voir `docs/CRH_CONSERVATION_CRH22_CRH36.md`. Ces défauts relèvent des extensions du fork ; aucune correction Vanilla n'est déduite.


## Conservation complète des tests métier CRH

Six tests avaient été écartés lors du premier portage par une détection trop large du mot teamworks. Les tests des événements, secrets et protections/actions/successions sont réintégrés sans changement métier. La qualification du socle passe de 278 à 319 tests, sous Windows et Linux, avec les deux tests exclusivement réseau réservés à leur suite SQL.


## Portage des écrans Démarches RH

Le cockpit, la création, les transitions, l'historique et le suivi des pièces de CRH-36 sont raccordés au menu Paramétrage de la coque actuelle. La fiche salarié et la fermeture sûre restent intactes. Le portage conserve la confirmation explicite avant écriture, les statuts métier/échange séparés, le refus des transitions périmées et la lecture seule des pièces après clôture.

Une erreur de rafraîchissement après une sauvegarde réussie ne doit plus annoncer une écriture échouée : le message indique que l'action est enregistrée et bloque les actions sur la projection périmée jusqu'à une actualisation. Cette famille est traitée pour création, transition, réception et retrait de pièce ; les erreurs de rechargement secondaires ne sont plus silencieuses. Il s'agit de composants nouveaux du fork, classés CCNS/extensions.

Trois parcours natifs complets sur une base SQLite jetable sont vérifiés, chacun avec six événements d'audit, ainsi que les annulations, l'état périmé, la clôture et les quatre échecs de rafraîchissement après écriture. Les confirmations sont automatisées par un dialogue wx générique de test. Les tests ne valent pas recette utilisateur et n'ouvrent aucune base réelle.


## Onglet Protection sociale dans le smoke de la fiche (14 octobre 2026)

L'onglet « Protection sociale » ajouté par `e2c59dc6` porte la fiche à neuf onglets. Le smoke Windows de la fiche en attendait encore huit et échouait avant d'atteindre le contrôle des pages. La liste attendue inclut maintenant cet onglet. Le parcours ouvre chaque onglet, donc charge aussi `CTRL_Page_protection_sociale_runtime`, et vérifie que `pageProtectionSociale` est construite. Un test statique aligne cette liste sur `DLG_Fiche_individuelle_lazy`. Défaut d'outillage d'une extension du fork : aucune correction Vanilla n'est déduite.
