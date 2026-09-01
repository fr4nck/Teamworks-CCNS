# Teamworks-CCNS — suivi CCNS et extensions

**Mise à jour : 1er septembre 2026**

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

## Extensions satellites en cours

Le chantier **Connexions RH** progresse séparément du build 0.9.1b en cours de qualification.

- `CRH-01` : modèle domaine des organismes, références non secrètes, périodes d'effet, liens de portail et profils de connexion ;
- `CRH-02` : descripteur de connecteur, capacités, modes, états et registre de découverte sans effet de bord ;
- `CRH-03` : dossiers de démarches RH, sujets personne/structure, pièces attendues, échéances et machine d'états métier distincte du statut technique d'échange ;
- `CRH-04` : événements d'audit immuables, journal append-only, cibles typées, horodatage avec fuseau et garde-fous contre les métadonnées manifestement secrètes ou médicales ;
- `CRH-05` : frontière d'échange de fichiers, formats versionnés, empreinte SHA-256, métadonnées d'artefacts sans payload, validation structurée et protocole d'adaptateur sans I/O implicite ;
- `CRH-06` : handles opaques de secrets, besoins de credentials et associations typées ; le domaine peut vérifier la disponibilité d'un handle sans lire la valeur secrète et ne définit encore aucun backend réel de coffre ;
- `CRH-07` : connecteur générique de portail manuel, préparation des références et pièces, demande d'ouverture uniquement après confirmation explicite, mise à jour manuelle de statut et événement d'audit sans simuler de transmission externe ;
- `CRH-08` : catalogue de connecteurs manuels de référence pour URSSAF, Net-entreprises, mutuelle, prévoyance, retraite complémentaire, OPCO, SPST et France Travail, sans annoncer d'API, de dépôt ou de synchronisation inexistants ;
- `CRH-09` : persistance additive de référence pour les profils non secrets, dossiers RH et événements append-only. Elle utilise un store SQLite dédié et versionné, sans modifier les bases historiques ni créer de clé étrangère vers les tables salariés/contrats ; ce store sert à qualifier le modèle persistant avant tout raccordement éventuel à la base principale ;
- `CRH-10A` : service applicatif de configuration d'une structure, avec port de repository et projections UI-agnostiques des organismes et connecteurs disponibles/configurés. Il prépare l'écran « Organismes & connexions RH » sans encore toucher à wxPython ;
- `CRH-11` : modèle historisable « Protection sociale & organismes » du salarié pour mutuelle, prévoyance, retraite complémentaire et SPST. Il distingue affiliation, dispense, enregistrement et suivi administratif, conserve périodes d'effet, régime/option, profil de cotisation, références externes, justificatif opaque, provenance et échéances, sans stocker de contenu médical ni de secret ;
- `CRH-12` : service applicatif salarié avec port de repository, cohérence obligatoire avec les organismes configurés de la structure, lecture tolérante de l'historique lorsque l'ancien profil a disparu, filtres des données effectives/échues et projection explicite des éléments pertinents pour une future préparation de paie, sans calcul de cotisation ;
- CRH-01 à CRH-08 restent sans persistance ; CRH-09 introduit uniquement le store isolé, CRH-10A l'orchestration structure, CRH-11 le modèle salarié et CRH-12 son orchestration applicative. Aucune authentification réelle, ouverture de navigateur effective ou communication réseau n'est ajoutée ;
- ces travaux ne modifient pas le pourcentage des 9 jalons CCNS ci-dessus et ne valent pas qualification fonctionnelle tant que leurs PR ne sont pas validées et fusionnées.

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

## Références principales

- `ROADMAP.md`
- `docs/48-revue-architecture-ccns.md`
- `docs/50-scope-metier.md`
- `docs/60-scenario-utilisation-controle-salarial.md`
- documentation `docs/40-*` à `docs/65-*`
