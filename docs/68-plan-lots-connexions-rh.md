# Plan de lots — Connexions RH et fondations « paie-ready »

**Date : 1er septembre 2026**

Ce document est un **plan de découpage technique** du chantier satellite « Connexions RH ». Il ne constitue pas une roadmap concurrente : `ROADMAP.md` reste l'unique roadmap d'exécution de Teamworks-CCNS et la validation Windows 0.9.1b reste le jalon prioritaire de qualification.

Le principe de conduite est simple : **la qualification 0.9.1b bloque une qualification de release, pas les développements satellites correctement isolés**.

## Objectifs

Le chantier doit permettre à Teamworks de mieux gérer les relations RH avec les organismes externes tout en préparant proprement les données qui pourraient, plus tard, alimenter une préparation de paie.

Il ne doit pas transformer Teamworks en logiciel de paie à ce stade.

Les objectifs sont :

- centraliser les organismes et portails RH d'une structure ;
- suivre affiliations, démarches, échéances, documents et statuts ;
- disposer d'un registre de connecteurs extensible ;
- supporter plusieurs niveaux d'intégration : lien, fichier, API, synchronisation ;
- conserver une traçabilité exploitable ;
- ne jamais imposer une connexion externe pour utiliser les fonctions RH locales ;
- rester multi-structures ;
- préparer progressivement les données utiles à une éventuelle production future de paie sans créer un moteur de paie inachevé.

## Règles de découpage

Chaque lot doit être :

- autonome ;
- testable ;
- réversible ;
- sans migration destructive ;
- sans secret stocké en clair ;
- sans dépendance obligatoire à un service externe ;
- sans branchement implicite sur un parcours critique existant ;
- activable progressivement ;
- documenté avec ses limites.

Les objets domaine restent indépendants de wxPython et de la persistance. Les adaptateurs externes vivent dans l'infrastructure. Les écrans ne portent pas les règles métier ni les protocoles d'échange.

## Voie A — lots satellites pouvant avancer pendant la qualification 0.9.1b

### CRH-01 — Modèle domaine des organismes

Créer un domaine dédié, par exemple `domain/hr_connections/`, sans persistance ni UI.

Objets envisagés :

- `HrOrganization` : organisme ou portail ;
- `OrganizationKind` : URSSAF, Net-entreprises, mutuelle, prévoyance, retraite, OPCO, SPST, France Travail, autre ;
- `OrganizationReference` : numéro d'adhérent, contrat, compte, établissement ou autre référence non secrète ;
- `ConnectorCapability` : lien, import, export, API, synchronisation, dépôt, téléchargement, statut ;
- `ConnectionProfile` : capacités déclarées pour une structure et un organisme ;
- `PortalLink` : URL et libellé du portail ;
- `EffectivePeriod` : dates d'effet et de fin lorsque pertinent.

Critères de sortie :

- zéro dépendance wxPython ;
- zéro accès réseau ;
- zéro mot de passe ;
- tests unitaires complets sur les invariants ;
- aucun effet sur le runtime historique tant que le domaine n'est pas appelé.

### CRH-02 — Registre des connecteurs

Créer un registre générique permettant de découvrir les capacités d'un connecteur sans connaître son implémentation.

Contrat minimal envisagé :

- identifiant stable du connecteur ;
- organisme ou famille d'organismes ;
- capacités annoncées ;
- version de l'adaptateur ;
- mode disponible : manuel, fichier, API ;
- état : disponible, désactivé, expérimental, non configuré ;
- vérification de configuration sans effet de bord.

Le registre ne doit ni ouvrir un navigateur ni appeler Internet lors de son import.

Critères de sortie : tests unitaires, enregistrement de faux connecteurs de test et absence d'effet de bord au chargement.

### CRH-03 — Dossiers et statuts de démarches RH

Introduire le modèle de dossier générique sans encore le brancher aux fiches salariés historiques.

Concepts :

- `HrCase` ou équivalent ;
- type de démarche ;
- personne ou structure concernée sous forme de référence métier ;
- organisme ;
- date d'ouverture ;
- échéance ;
- statut ;
- résultat ;
- commentaire ;
- source ;
- pièces attendues ;
- événements de suivi.

Cycle de base proposé :

`À faire → préparé → transmis → accepté`

avec branches :

`anomalie → régularisation → accepté`

et états techniques explicites lorsqu'une transmission automatisée existe.

Le modèle doit distinguer le statut métier du statut technique d'un échange.

### CRH-04 — Journal d'événements et traçabilité

Préparer un journal append-only au niveau domaine/service pour les événements sensibles :

- création de dossier ;
- changement de statut ;
- ajout/retrait de pièce ;
- génération d'export ;
- import de retour ;
- lancement d'une synchronisation ;
- résultat d'une synchronisation ;
- changement de configuration d'un connecteur.

Ne jamais journaliser un secret, mot de passe, jeton, cookie de session ou contenu médical sensible non nécessaire.

### CRH-05 — Formats d'échange et adaptateurs de fichiers

Créer une frontière générique pour les échanges de fichiers :

- export ;
- import ;
- validation de format ;
- métadonnées ;
- empreinte du fichier ;
- date de génération/réception ;
- résultat de validation ;
- erreurs structurées.

Les premiers adaptateurs peuvent être des formats internes de test. L'objectif est de stabiliser la frontière avant d'implémenter un format réglementaire réel.

### CRH-06 — Sécurité des identifiants et secrets

Définir l'architecture de sécurité avant toute authentification réelle.

Principes :

- aucune donnée secrète dans les tables métier ;
- aucune donnée secrète dans les logs ;
- aucune donnée secrète dans les exports de diagnostic ;
- distinction entre référence de compte non secrète et credential ;
- abstraction `SecretStore` ou équivalente ;
- possibilité de backend système ou coffre dédié ultérieur ;
- absence de secret = connecteur non configuré, jamais erreur fatale pour Teamworks.

Ce lot peut rester purement contractuel et testé tant qu'aucun backend réel n'est requis.

### CRH-07 — Connecteur générique « portail manuel »

Premier connecteur réellement utile sans API :

- affiche le portail officiel configuré ;
- expose la liste des démarches disponibles ;
- permet de préparer les pièces et références ;
- ouvre éventuellement le navigateur à la demande explicite de l'utilisateur ;
- permet d'enregistrer manuellement le statut et le numéro de dossier ;
- journalise l'action sans prétendre qu'une transmission a été automatisée.

Ce connecteur sert de solution de repli commune à tous les organismes.

### CRH-08 — Connecteurs de référence sans authentification automatisée

Décliner le modèle pour les familles suivantes, sans scraping ni automatisation fragile :

- URSSAF ;
- Net-entreprises ;
- mutuelle ;
- prévoyance ;
- retraite complémentaire ;
- OPCO ;
- SPST / PST35 ;
- France Travail.

Chaque connecteur peut n'annoncer au départ que `DEEP_LINK`, `DOCUMENT_EXPORT`, `DOCUMENT_IMPORT` ou `MANUAL_STATUS` selon ce qui est réellement supporté.

Aucune capacité ne doit être déclarée disponible si elle n'est pas testée.

## Voie B — lots à raccorder après validation ou sous branche dédiée avec vigilance renforcée

Ces lots commencent à toucher les données ou parcours RH existants. Ils restent possibles en parallèle, mais ne doivent pas être fusionnés machinalement dans un `master` en cours de qualification.

### CRH-09 — Persistance additive

Ajouter uniquement les tables réellement nécessaires aux lots validés :

- organismes de la structure ;
- références non secrètes ;
- dossiers RH ;
- événements de dossier ;
- pièces et métadonnées ;
- configuration non secrète de connecteur.

Conditions :

- schéma additif ;
- compatibilité MySQL/MariaDB et chemins historiques concernés ;
- aucune modification destructive ;
- migrations idempotentes ;
- tests de création, lecture, mise à jour et rollback logique ;
- sauvegarde/restauration vérifiées si le schéma entre dans la base principale.

### CRH-10 — Rattachement à la structure

Ajouter dans les paramètres d'organisation un écran « Organismes & connexions RH » permettant de gérer :

- organisme ;
- type ;
- références ;
- contrats ;
- dates d'effet ;
- liens ;
- contact ;
- capacités du connecteur ;
- statut de configuration.

Aucun secret ne doit être visible ou exporté avec les données métier ordinaires.

### CRH-11 — Rattachement salarié « Protection sociale & organismes »

Ajouter progressivement à la fiche salarié :

- mutuelle : affiliation/dispense, dates, justificatif ;
- prévoyance : régime applicable ;
- SPST : suivi administratif et échéances ;
- dossiers liés à la personne ;
- historique des démarches.

Ce lot touche un parcours critique de recette et doit donc bénéficier d'une recette wxPython spécifique, tests de persistance et contrôle de non-régression sur la fiche individuelle.

### CRH-12 — Tableau de bord des démarches

Créer un cockpit transversal :

- démarches à faire ;
- échéances proches ;
- dossiers en anomalie ;
- pièces manquantes ;
- retours reçus ;
- dernières synchronisations ;
- filtres par structure, organisme, salarié et statut.

Ce tableau de bord consomme les données du domaine ; il ne doit pas contenir les protocoles des connecteurs.

### CRH-13 — Déclencheurs de cycle de vie salarié

À partir d'événements RH existants, proposer des tâches sans automatiser aveuglément :

Embauche :

- DPAE / URSSAF ;
- mutuelle ou dispense ;
- prévoyance ;
- SPST ;
- éventuel dossier OPCO ;
- pièces contractuelles ;
- suivi déclaratif à venir.

Fin de contrat :

- radiation ou maintien selon le régime ;
- portabilité lorsqu'elle s'applique ;
- documents de fin de contrat ;
- France Travail ;
- fermeture des dossiers concernés.

Arrêt ou accident : création guidée des démarches pertinentes sans présumer du canal de transmission.

Chaque déclencheur doit être idempotent : rouvrir une fiche ou recalculer un état ne doit pas créer de doublons.

## Voie C — préparation de paie, sans moteur de paie

### PRH-01 — Éléments variables de rémunération

Introduire cet objet uniquement lorsqu'un besoin RH concret le justifie.

Champs minimaux :

- salarié ;
- période ;
- type ;
- quantité ;
- unité ;
- montant/taux éventuel ;
- date d'effet ;
- source ;
- justificatif ;
- commentaire ;
- statut de validation.

Le système collecte et contrôle ; il ne calcule pas encore un bulletin.

### PRH-02 — Historisation de rémunération et situation contractuelle

Éviter l'écrasement silencieux des valeurs ayant un effet potentiel sur la paie :

- salaire/taux ;
- classification ;
- temps contractuel ;
- primes régulières ;
- changement de statut ;
- dates d'effet.

La migration doit se faire uniquement lorsqu'un besoin fonctionnel réel touche ces données.

### PRH-03 — Export mensuel « préparation de paie »

Produire un export contrôlé et explicable regroupant :

- situation contractuelle de la période ;
- temps ;
- absences ;
- variables validées ;
- frais/indemnités lorsque pertinents ;
- protection sociale utile ;
- anomalies ou informations manquantes.

L'export doit être traçable, versionné et reproductible pour une même période et un même état des données.

### PRH-04 — Rapprochement avec la paie de référence

Permettre ultérieurement d'importer des résultats ou variables provenant du prestataire/logiciel de paie afin de comparer :

- variables préparées ;
- éléments réellement pris en compte ;
- écarts ;
- corrections ;
- historique des régularisations.

Cette étape est importante avant toute décision sur une paie native.

## Voie D — intégrations officielles, une par une

Une API ou un échange automatisé n'est ajouté que si :

- un canal officiel et documenté existe ;
- son authentification est compatible avec l'architecture de sécurité ;
- son usage est juridiquement et contractuellement autorisé ;
- les erreurs et indisponibilités sont gérées ;
- un mode manuel ou fichier reste possible lorsqu'il est nécessaire ;
- le connecteur est testé sans rendre Teamworks dépendant du service.

Ordre indicatif à réévaluer selon disponibilité réelle des interfaces :

1. formats de fichiers simples et stables réellement utilisés ;
2. retours structurés importables ;
3. API officielles accessibles et documentées ;
4. synchronisation de statuts ;
5. dépôts automatisés uniquement lorsque le canal le permet explicitement.

Aucun scraping d'interface Web ne constitue une fondation acceptable pour une fonction RH critique.

## Hors périmètre actuel

Restent explicitement hors chantier tant qu'une décision distincte n'est pas prise :

- calcul brut/net ;
- moteur de cotisations ;
- bulletin natif ;
- DSN native ;
- dépôt DSN automatisé ;
- PAS calculé par Teamworks ;
- remplacement du logiciel ou prestataire de paie.

## Ordre de réalisation recommandé

Séquence satellite recommandée :

**CRH-01 → CRH-02 → CRH-03 → CRH-04 → CRH-05 → CRH-06 → CRH-07 → CRH-08**.

Ces huit lots peuvent être développés essentiellement hors des parcours wxPython critiques.

Après validation de la 0.9.1b, ou sur branches explicitement séparées avec requalification avant fusion :

**CRH-09 → CRH-10 → CRH-11 → CRH-12 → CRH-13**.

Puis, lorsque les besoins RH le justifient :

**PRH-01 → PRH-02 → PRH-03 → PRH-04**.

Les intégrations officielles de la voie D se branchent ensuite sur cette architecture au cas par cas.

## Premier incrément conseillé

Le premier incrément de code doit rester volontairement petit :

1. `domain/hr_connections/` ;
2. types d'organismes ;
3. capacités de connecteurs ;
4. contrat du registre ;
5. faux connecteur de test ;
6. tests unitaires ;
7. aucune persistance ;
8. aucune UI ;
9. aucun réseau ;
10. aucun secret.

Ce lot constitue la fondation la plus sûre pour commencer le développement immédiatement sans interférer avec la recette Windows en cours.
