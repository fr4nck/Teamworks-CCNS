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
- `CRH-10B` : écran wxPython « Organismes & connexions RH » accessible depuis le paramétrage. Il crée et modifie les profils non secrets de la structure active, références administratives, périodes d'effet et portails ; code et famille sont figés après création, aucune suppression de profil n'est proposée et aucune capacité API/dépôt/synchronisation ne peut être activée déclarativement ;
- `CRH-11` : modèle historisable « Protection sociale & organismes » du salarié pour mutuelle, prévoyance, retraite complémentaire et SPST. Il distingue affiliation, dispense, enregistrement et suivi administratif, conserve périodes d'effet, régime/option, profil de cotisation, références externes, justificatif opaque, provenance et échéances, sans stocker de contenu médical ni de secret ;
- `CRH-12` : service applicatif salarié avec port de repository, cohérence obligatoire avec les organismes configurés de la structure, lecture tolérante de l'historique lorsque l'ancien profil a disparu, filtres des données effectives/échues et projection explicite des éléments pertinents pour une future préparation de paie, sans calcul de cotisation ;
- `CRH-13` : adaptateur SQLite de référence dédié aux suivis salarié. Il persiste les périodes d'effet et métadonnées payroll-ready dans un schéma versionné, isolé des bases historiques et sans clé étrangère vers les profils d'organismes afin de préserver l'historique. Ce store séparé sert uniquement à qualifier le contrat de persistance ; le raccordement de production devra consolider les adaptateurs dans la base cible plutôt que multiplier les fichiers locaux ;
- `CRH-14` : synthèse descriptive UI-agnostique du suivi salarié. Elle prépare les lignes et compteurs du futur onglet, distingue données effectives, en attente, échues, payroll-ready et références d'organismes orphelines, sans conclure automatiquement à une obligation ou conformité juridique ;
- `CRH-15` : premier composant wxPython de consultation « Protection sociale & organismes ». Le panneau consomme uniquement la projection CRH-14, utilise les tokens sémantiques du design system et ne choisit ni backend, ni transport réseau, ni règle de conformité ;
- `CRH-16` : adaptateur de persistance de production `TeamworksHrConnectionsRepository` au-dessus de `GestionDB`. Il consolide dans la base Teamworks active les profils non secrets d'organismes et les suivis salarié, avec schéma additif versionné, transactions, index ciblés et adaptation des paramètres SQLite/MySQL. Aucune table historique n'est modifiée et aucune clé étrangère n'est créée vers les personnes ou contrats ;
- `CRH-17A` : identité stable et non secrète de la structure portée par la base active, puis point de composition `EmployeeProtectionSummaryRuntimeFactory`. L'identité est un UUID opaque stocké dans `tw_hr_structure_identity` et n'est jamais dérivée du chemin local, du nom/hôte de base ou des paramètres réseau historiques ;
- `CRH-17B` : raccordement différé de la synthèse « Protection sociale » à la fiche individuelle salarié. L'ouverture de la fiche n'importe pas le runtime Connexions RH et une erreur du sous-système reste contenue dans l'onglet ;
- `CRH-18` : frontière d'écriture contrôlée du suivi salarié avec création et clôture d'une période active, sans édition libre ni suppression ;
- `CRH-19` : succession transactionnelle des périodes de protection sociale : clôture du prédécesseur et insertion du successeur dans une seule unité de travail, avec rollback intégral en cas d'échec ;
- `CRH-20` : actions wxPython « Ajouter », « Clôturer » et « Nouvelle période » raccordées à l'onglet salarié. Le dialogue reste séparé de la persistance et les écritures sont chargées uniquement au premier clic ;
- `CRH-21` : projection UI-agnostique du cockpit structure des démarches RH. Elle distingue compteurs métier et échecs techniques, dossiers échus, organismes orphelins et nombres de pièces attendues sans inventer de présence documentaire ni de conformité ; elle reste indépendante de wxPython et de la persistance de production des dossiers ;
- `CRH-22` : adaptateur de persistance de production `TeamworksHrCasesRepository` pour les dossiers CRH-03, pièces attendues et événements CRH-04. Il s'appuie sur `GestionDB`, conserve la compatibilité SQLite/MySQL, versionne un schéma strictement additif et maintient le journal d'audit append-only sans clé étrangère vers les données historiques ;
- `CRH-23` : runtime de lecture du cockpit sur la base Teamworks active. Il compose l'identité stable de la structure, la persistance des démarches, les organismes configurés et la projection CRH-21 derrière une façade qui exige une date de référence explicite et n'expose aucune opération d'écriture ;
- `CRH-24` : premier cockpit wxPython « Démarches RH » en lecture seule. Il affiche compteurs, échéances, anomalies métier, échecs techniques, organismes non configurés et détail descriptif des dossiers sans connaître la persistance ni proposer de transition de workflow ;
- `CRH-25` : service et runtime de workflow contrôlé des démarches. Les transitions autorisées restent définies par `HrCase`, la projection courante et l'événement d'audit sont persistés atomiquement, et un contrôle optimiste sur les statuts métier/technique refuse les écrasements concurrents ;
- `CRH-26` : actions wxPython du cockpit « Démarches RH ». Le bouton « Faire évoluer » charge le runtime d'écriture au premier clic, ne propose que les transitions autorisées par le domaine, exige une confirmation explicite, conserve résultat/commentaire, recharge le cockpit après écriture et ne modifie jamais le statut technique d'échange ;
- CRH-01 à CRH-08 restent sans persistance ; CRH-09 et CRH-13 restent des stores de qualification isolés. CRH-16 fournit l'adaptateur de production pour les profils et suivis salarié, CRH-22 celui des démarches et événements. CRH-17A verrouille l'identité logique de la base. CRH-10A orchestre la structure et CRH-10B l'expose au paramétrage ; CRH-11 à CRH-20 construisent le suivi salarié jusqu'aux actions historisées ; CRH-21 à CRH-26 construisent le cockpit structure, sa persistance, sa frontière transactionnelle et ses premières actions métier. Aucune authentification réelle, ouverture de navigateur effective ou communication réseau n'est ajoutée ;
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
- documentation `docs/40-*` à `docs/78-*`
