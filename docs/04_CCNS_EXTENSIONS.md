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
