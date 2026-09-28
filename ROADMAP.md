# Teamworks-CCNS — Roadmap officielle et unique

**Mise à jour : 28 septembre 2026**

Ce fichier est l’unique roadmap d’exécution de Teamworks-CCNS. Il décrit l’état réel du produit et l’ordre des travaux. Les décisions d’architecture transverses entre Teamworks, Noethys, Portail/Connecthys, PMSL Équipe et les services externes relèvent de `fr4nck/PMSL-Arch`.

La roadmap ne confond jamais : code préparé, tests automatisés, build produit, recette terrain et fonction disponible en production.

## 1. Recalage de septembre 2026

La roadmap du 31 août n’est plus représentative du projet. Depuis, plusieurs rails structurants ont été ouverts en parallèle : stabilisation finale de la Vanilla wx 0.9.2, Qt Vanilla, migration Noethys/Teamworks, Contrats avancés, Présences, Frais, Documents RH, Scénarios, habilitations, DPAE et sorties salarié / Impact Emploi.

Le projet n’est pas considéré comme « en retard » par rapport à l’ancienne roadmap : c’est la roadmap qui était devenue désynchronisée du périmètre réel.

À compter de cette révision :

- une idée ou une étude n’est pas automatiquement un chantier actif ;
- une PR draft n’est pas une fonction livrée ;
- les piles de PR doivent être terminées ou arbitrées avant d’ouvrir de nouveaux rails majeurs ;
- les recettes Windows/MySQL réelles restent des stop-gates lorsqu’elles sont prévues ;
- aucun pourcentage global d’avancement n’est utilisé ;
- aucune date de sortie n’est annoncée sans preuve suffisante.

## 2. État de référence

`master` reste la vérité intégrée du dépôt.

Au 28 septembre 2026 :

- `VERSION` sur `master` : **0.9.1f** ;
- dernier commit observé sur `master` : **`09ad795ec5c4729230a68cfeac6faa0e6634dba2`**, correction CI pour réserver MkDocs aux changements de documentation ;
- la documentation MkDocs est intégrée à `master` ;
- de nombreux travaux récents restent volontairement en PR draft et ne doivent pas être présentés comme intégrés ;
- la Vanilla wx 0.9.2 RC3 existe comme candidate de clôture dans la PR #430, mais sa situation doit rester distinguée de `master` ;
- la Qt Vanilla 0.1 existe comme candidate intégrée dans la PR #467, avec ses recettes terrain encore nécessaires ;
- DPAE et Sorties salarié / Impact Emploi sont désormais deux domaines structurants explicites du programme.

## 3. Ordre de priorité

La roadmap est désormais organisée en quatre horizons : **MAINTENANT**, **ENSUITE**, **PLUS TARD**, **PARKING**.

L’objectif est de réduire le travail en cours, fermer les boucles de qualification et empêcher qu’une nouvelle étude déplace implicitement les priorités.

# MAINTENANT — fermer les boucles déjà ouvertes

## M1 — Stabiliser la base d’exécution et la CI

Objectif : disposer d’un socle de référence fiable pour juger toutes les piles de PR.

À faire :

- vérifier les runs du HEAD exact de chaque PR active avant toute décision de merge ;
- conserver le workflow CI unique ;
- distinguer les échecs de code des limites/configurations GitHub ;
- ne pas laisser MkDocs ou le packaging masquer le résultat réel des tests métier ;
- maintenir `master` comme base intégrée lisible.

Critère de sortie : les piles actives peuvent être évaluées sans ambiguïté sur leur SHA, leurs tests et leurs dépendances.

## M2 — Clôturer la Vanilla wx 0.9.2

PR de référence : **#430 — 0.9.2 RC3 — clôture Vanilla wx**.

La Vanilla wx reste le produit historique à sécuriser tant que Qt n’a pas franchi ses recettes terrain et atteint le périmètre nécessaire.

À faire :

- rejouer les parcours de recette Windows réellement nécessaires ;
- valider MySQL réel et les intégrations natives utilisées en exploitation, notamment Word/LibreOffice lorsqu’elles sont dans le parcours ;
- traiter uniquement les anomalies bloquantes ou les régressions démontrées ;
- arrêter d’ajouter de nouvelles fonctions métier à la Vanilla sauf nécessité de production ;
- décider explicitement de la clôture de la branche RC3 et de son statut de release.

Les anciennes PR RC1/RC2 et correctifs wx restent des preuves/historique ou des dépendances à consolider ; elles ne constituent pas autant de nouveaux rails indépendants.

## M3 — Qualifier Qt Vanilla 0.1 sur l’environnement réel

PR d’intégration de référence : **#467 — Qt Vanilla 0.1 RC**.

Les gates automatisés décrits dans cette PR sont largement préparés. Le verrou principal est désormais la preuve terrain :

- version MySQL réellement utilisée en exploitation ;
- copie représentative et autorisée ;
- recette Windows réelle ;
- vérification avant/après de la base ;
- absence de mutation inattendue du schéma ou des données ;
- PV de recette.

Qt Vanilla 0.1 ne doit pas être qualifiée stable sur la seule base de la CI.

## M4 — Terminer le socle DPAE avant le protocole externe

Pile active :

- **#477 — DATA-001 V2** : Case / Submission / Return, concurrence, idempotence et snapshots ;
- **#478 — DATA-002A** : capture des données déclaratives nécessaires ;
- **#481 — Incident Recovery** : récupération des `SENDING` interrompus ;
- **#482 — erreurs applicatives structurées**.

Règle : **GATE PROTOCOLE NON LEVÉ** tant que le contrat réel DPAE-EDI 120, le XSD, le transport, l’authentification et les contraintes Urssaf ne sont pas vérifiés et documentés.

À faire avant d’élargir :

- stabiliser et revoir la pile DATA ;
- obtenir les garanties MySQL/MariaDB réellement revendiquées ;
- consolider les erreurs opérateur ;
- documenter précisément ce qui est source de vérité Teamworks et ce qui est snapshot déclaratif ;
- seulement ensuite ouvrir XML/XSD/transport.

Aucun endpoint, secret ou comportement réseau ne doit être inventé.

## M5 — Construire le parcours Sortie salarié / Impact Emploi

Pile active :

- **#479 — SORTIE-001** : socle métier ;
- **#483 — SORTIE-002** : persistance MySQL/MariaDB et concurrence ;
- **#484 — SORTIE-003** : snapshots immuables de communication à Impact Emploi et corrections versionnées.

Le domaine doit rester distinct de `Contract.end_date` et de DPAE.

Ordre retenu :

1. consolider SORTIE-001 ;
2. consolider SORTIE-002 ;
3. consolider SORTIE-003 ;
4. réaliser **SORTIE-004** : documents, réception/contrôle de l’AER, clôture réelle et anomalies ;
5. raccorder ensuite l’UI opérateur ;
6. seulement après, étudier les automatismes supplémentaires autour de DSN/FCTU si une source et une responsabilité réelles sont établies.

Le modèle doit distinguer explicitement : décision/notification, fin effective, date de connaissance, préparation, communication à Impact Emploi, réception de l’AER et clôture.

# ENSUITE — converger les rails Qt et l’architecture

## E1 — Contrats avancés Qt

Pile : **#448, #455, #457, #460, #462, #464**.

Le code préparatoire est largement qualifié automatiquement, mais l’activation reste bloquée par le stop-gate Windows/MySQL réel du Rail A.

Ordre :

1. recette Windows/MySQL réelle ;
2. CEE ;
3. renouvellement CDD et CDD → CDI ;
4. classification / valeur de point ;
5. période d’essai complète ;
6. activation explicite du feature gate ;
7. recette de non-régression après activation.

Aucun contournement du stop-gate n’est admis.

## E2 — Présences et futur Planning Qt

PR de référence : **#450**.

Le métier d’écriture, le contrat de lecture, le CRUD Qt et la concurrence optimiste sont déjà fortement préparés.

Suite :

- recette sur base représentative ;
- stabiliser le CRUD Présences ;
- utiliser les contrats de lecture/écriture existants pour construire le futur Planning ;
- ne pas porter `CTRL_Planning.py` comme un monolithe dans Qt ;
- traiter ensuite les besoins planning avancés, banques de récupération et règles CCNS/CEE avec des contrats métier explicites.

## E3 — Frais / remboursements

PR de référence : **#444**.

Le CRUD transactionnel et une qualification MySQL moderne existent. Reste à :

- confirmer la version MySQL d’exploitation ;
- tester une copie de données représentative ;
- vérifier les variantes historiques `NULL/0`, codes postaux et montants ;
- décider séparément du cache auxiliaire `distances`.

## E4 — Documents RH / publipostage

PR : **#452** puis **#453**.

Objectif : conserver un moteur documentaire commun testable, puis brancher les sorties natives nécessaires sans réintroduire la logique métier dans wx ou Qt.

Ordre : moteur commun → contexte/modèles Qt → génération réelle → Word/LibreOffice si requis → recette Windows native.

## E5 — Scénarios

PR de référence : **#446**.

Le moteur transactionnel est préparé. Le raccord UI Qt et la recette réelle viennent après les rails nécessaires à Qt Vanilla et non avant eux.

## E6 — Personnes, recherche et habilitations

PR concernées : **#472, #473, #474, #475, #476**.

Ces travaux forment un même axe de convergence :

- autorisations explicites et refus par défaut ;
- recherche de personnes indépendante de l’UI ;
- use cases Personnes hors wx ;
- rafraîchissement wx sans reconstruction inutile de l’interface ;
- réutilisation future côté Qt.

Avant merge, vérifier les bases empilées et éviter de maintenir plusieurs branches concurrentes portant les mêmes extractions.

## E7 — Migration Noethys / Teamworks

PR de référence : **#454**.

La stratégie reste non destructive : inventaire, traçabilité ligne par ligne, import reproductible depuis copie/snapshot, aucune conversion en place.

Étape suivante : qualification contre le vrai environnement historique, en particulier MySQL 5.5 si c’est encore la version réellement déployée, puis extension progressive du pilote Frais.

La migration ne doit pas devenir un prétexte pour redéfinir simultanément tous les domaines métier.

# PLUS TARD — après fermeture des stop-gates actuels

Les sujets suivants restent légitimes mais ne doivent pas concurrencer les lots MAINTENANT :

- parité fonctionnelle Qt plus large avec la Vanilla wx ;
- Planning graphique complet ;
- CRUD Scénarios Qt complet ;
- automatisation documentaire Office/LibreOffice Qt ;
- extension de la migration historique à d’autres domaines ;
- formulaires/questionnaires conditionnels communs ;
- approfondissement des banques de récupération, minicamps et règles conventionnelles après stabilisation du moteur Planning ;
- facturation électronique : veille et cadrage d’architecture uniquement tant que le périmètre Teamworks n’est pas démontré ;
- convergence plus large de la suite PMSL, à arbitrer dans PMSL-Arch et non dans cette roadmap seule.

# PARKING — idées à ne pas transformer en chantier sans arbitrage

Une idée entre ici lorsqu’elle est intéressante mais sans besoin immédiat, dépendance résolue ou preuve de priorité.

Exemples actuels :

- refonte visuelle supplémentaire de la Vanilla wx ;
- réécriture générale de composants historiques qui fonctionnent sans incident démontré ;
- nouveaux moteurs génériques avant qu’un deuxième consommateur réel les justifie ;
- automatisation complète de flux externes dont le protocole réel n’est pas acquis ;
- changement global d’ERP, intégration Dolibarr/WordPress ou transformation de la suite en plateforme générique sans étude dédiée PMSL-Arch.

## 4. Règles de gouvernance des nouveaux travaux

Avant d’ouvrir un nouveau rail majeur, répondre explicitement à cinq questions :

1. quel problème utilisateur ou d’exploitation est démontré ?
2. pourquoi ce problème passe-t-il devant les stop-gates en cours ?
3. quel est le plus petit lot livrable ?
4. quelle preuve permettra de déclarer ce lot terminé ?
5. quel chantier actif est fermé, suspendu ou repoussé en contrepartie ?

Sans réponse satisfaisante, le sujet va dans PLUS TARD ou PARKING.

## 5. Politique de PR

- les PR draft peuvent servir à préparer et qualifier un lot ;
- une pile de PR doit annoncer explicitement sa base et son ordre de merge ;
- aucune PR empilée ne doit être mergée avant sa base ;
- les PR techniques de CI ne sont pas des fonctions produit ;
- les anciennes PR supersédées doivent être fermées lorsqu’elles ne servent plus de base réelle ;
- un merge n’équivaut pas à une recette utilisateur ;
- les SHA et runs exacts priment sur les affirmations générales de maturité.

## 6. Définition de « terminé »

Un lot n’est terminé que lorsque les preuves nécessaires à son niveau sont acquises :

- métier pur : tests contractuels et invariants ;
- persistance : tests transactionnels et moteur SQL réellement revendiqué ;
- UI : parcours natif sur l’OS concerné ;
- intégration externe : protocole réel vérifié, erreurs et reprise documentées ;
- release : build reproductible + recette terrain + absence de blocant connu + décision explicite de qualification.

## 7. Cap produit

La trajectoire reste :

1. maintenir une Vanilla wx exploitable pendant la transition ;
2. déplacer progressivement les règles métier vers des couches communes indépendantes de wx/Qt ;
3. qualifier Qt sur les données et l’environnement réels avant d’étendre son périmètre ;
4. fiabiliser les processus RH réglementaires prioritaires, notamment DPAE et sorties salarié ;
5. migrer les données historiques sans perte ni conversion opaque ;
6. réduire progressivement la dépendance au code UI historique sans réécriture massive non justifiée.

La priorité n’est plus d’ouvrir davantage de fronts. Elle est de **transformer les travaux déjà engagés en chaînes terminées, recettées et compréhensibles**.
