# Teamworks-CCNS — suivi CCNS et extensions

**Mise à jour : 31 août 2026**

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

## Direction après stabilisation — socle RH « paie-ready »

La direction fonctionnelle retenue est de **ne pas lancer maintenant un véritable moteur de paie**. Teamworks doit d'abord exécuter correctement et durablement ses fonctions RH actuelles.

En revanche, les futurs lots RH doivent conserver, lorsqu'elles sont utiles au besoin traité, les données qui pourraient servir plus tard à la préparation ou au contrôle d'un bulletin : historique contractuel, rémunération, temps, absences, variables, avantages, protection sociale, organismes, dates d'effet, sources et justificatifs.

Cette discipline vise à éviter une reconstruction ultérieure du modèle RH si une paie native est décidée un jour. Elle ne vaut ni décision de produire des bulletins, ni décision de générer la DSN, ni remplacement du système de paie actuel.

Le cadrage détaillé est défini dans `docs/67-fondations-rh-paie-ready.md`.

Cette orientation **ne modifie pas le calcul d'avancement ci-dessus** et ne passe pas devant la recette réelle de la version 0.9.1b.

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
- `docs/67-fondations-rh-paie-ready.md`
- documentation `docs/40-*` à `docs/65-*`