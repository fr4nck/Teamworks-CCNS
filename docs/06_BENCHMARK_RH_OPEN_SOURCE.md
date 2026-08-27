# Benchmark RH open source — idées transférables à Teamworks-CCNS

**Statut : document vivant**  
**Créé : 27 août 2026**

> Ce document n'est pas une roadmap concurrente de `ROADMAP.md`. Il sert de mémoire de recherche et de source d'idées. Toute intégration réelle devra être arbitrée puis inscrite séparément dans la roadmap officielle.

## 1. Garde-fou de périmètre

Teamworks-CCNS reste un outil **RH** : salariés, contrats, temps de travail, compétences/diplômes, absences, obligations employeur, contraintes CCNS et données administratives RH.

Il ne doit pas absorber :
- la facturation ou les prestations métier ;
- la gestion d'activités ALSH/sportives ;
- le planning opérationnel des séances ;
- la recherche de remplaçants opérationnels ;
- les fonctions métier relevant de Noethys ou de PMSL Équipe.

Le benchmark vise donc uniquement des fonctions RH transférables sans brouiller cette séparation.

## 2. Première passe — petits projets RH inspectés

Dépôts exploratoires déjà étudiés : `staff-manager`, `humanresource`, `HRMS`, `Employee-Attendance-Management`.

Enseignements retenus :
- dossier salarié structuré par sous-domaines ;
- contacts d'urgence ;
- historique d'emploi daté ;
- workflow de congés avec états ;
- compteurs par type d'absence ;
- absences possibles en heures / fractions de journée ;
- archivage plutôt que suppression brutale ;
- organisation par services / fonctions ;
- recherche et actions RH en masse.

Les idées les plus fortes de cette première passe sont :
1. une **ligne de vie RH** historisée ;
2. un **moteur d'absences et congés** avec mouvements de compteur ;
3. un **dossier salarié enrichi** ;
4. un **cockpit d'échéances RH**.

## 3. OrangeHRM — dossier salarié composable + RGPD

Dépôt : `orangehrm/orangehrm` — OrangeHRM Starter, GPL.

### Concepts observés

OrangeHRM découpe le dossier du salarié en entités dédiées :
- contact d'urgence ;
- personnes à charge ;
- expérience professionnelle ;
- formation ;
- compétences ;
- langues ;
- licences / habilitations avec dates ;
- adhésions ;
- rémunération ;
- rattachements / localisation ;
- contrat ;
- hiérarchie ;
- évaluations ;
- congés ;
- présence.

Cette structure confirme qu'une fiche salarié robuste gagne à être **composée de sous-dossiers spécialisés** plutôt qu'à devenir un formulaire unique surchargé.

### Idée particulièrement importante : RGPD intégré au SIRH

OrangeHRM possède des stratégies explicites :
- d'**accès/export** des données d'un salarié ;
- de **purge/anonymisation** des données personnelles, champ par champ et entité par entité.

La purge ne signifie pas forcément supprimer toute trace : certaines données sont détruites, d'autres anonymisées afin de préserver la cohérence historique.

### Transposition Teamworks-CCNS

À retenir :
- export « dossier personnel » d'un salarié ;
- politique de conservation par type de donnée ;
- anonymisation contrôlée d'un ancien salarié ;
- destruction séparée des pièces jointes et données très personnelles ;
- maintien des éléments strictement nécessaires à l'historique légal ou statistique ;
- droits d'accès distincts pour les données sensibles.

**Priorité conceptuelle : élevée.**

## 4. Frappe HR — cycle de vie salarié et journal de congés

Dépôt : `frappe/hrms` — solution RH open source moderne.

### Cycle de vie salarié

Frappe HR traite explicitement :
- recrutement ;
- offre d'emploi ;
- onboarding ;
- salarié ;
- promotions ;
- transferts ;
- séparation / départ ;
- entretien de sortie.

Il existe donc un véritable **cycle de vie RH**, et non une simple fiche dont les valeurs courantes écrasent les précédentes.

### Onboarding / offboarding sous forme de workflow

L'onboarding contient :
- un modèle réutilisable ;
- une liste d'activités ;
- une date de début ;
- une durée ;
- un responsable utilisateur ou rôle ;
- des tâches générées automatiquement ;
- des échéances ajustées en fonction des jours non travaillés ;
- un statut `Pending / In Process / Completed` ;
- la possibilité de notifier les responsables.

Le même contrôleur sert au départ du salarié.

### Journal des congés

Frappe HR possède un `Leave Ledger Entry` : chaque mouvement rattache :
- un salarié ;
- un type de congé ;
- une origine de transaction ;
- une quantité ;
- une période ;
- un éventuel report ;
- une expiration ;
- le caractère sans solde.

Cette architecture valide fortement l'idée de **calculer un solde à partir d'un journal de mouvements** plutôt que de stocker un nombre éditable sans traçabilité.

### Transposition Teamworks-CCNS

À retenir :
- checklist d'arrivée ;
- checklist de départ ;
- responsable + échéance pour chaque action RH ;
- modèles selon le type de salarié / contrat ;
- historique des promotions / changements d'affectation ;
- journal transactionnel des droits à absence.

**Priorité conceptuelle : très élevée.**

## 5. Horilla HRMS — discipline, audit et processus RH plus larges

Dépôt : `horilla/horilla-hr` — LGPL, branche 2.0 active.

### Fonctions visibles

Horilla couvre notamment :
- gestion des salariés ;
- recrutement complet ;
- onboarding / offboarding ;
- présence et temps ;
- congés ;
- paie ;
- performance ;
- actifs confiés ;
- helpdesk RH ;
- journalisation / audit ;
- actions disciplinaires.

Le dépôt contient un véritable domaine `disciplinary_actions`, avec types d'action, formulaires, listes, filtres et dossiers disciplinaires.

### Transposition Teamworks-CCNS

À retenir avec prudence :
- **journal d'audit** des modifications RH sensibles ;
- **dossier disciplinaire** séparé du dossier courant du salarié ;
- dates, nature de l'action, documents et historique ;
- droits d'accès renforcés ;
- meilleure continuité entre recrutement, arrivée et dossier salarié.

À ne pas reprendre automatiquement :
- helpdesk généraliste ;
- badgeuse / biométrie ;
- paie complète ;
- gestion générale des actifs, sauf besoin RH démontré.

**Priorité : audit élevé ; discipline à évaluer fonctionnellement et juridiquement.**

## 6. Sentrifugo — modules séparés et gestion de sortie

Dépôt : `Sentrifugo/sentrifugo`.

Projet plus ancien, mais intéressant comme référence fonctionnelle. Son architecture sépare notamment :
- `assets` ;
- `exit` ;
- `expenses` ;
- `timemanagement`.

L'intérêt n'est pas technologique, mais métier : un **départ salarié** mérite un domaine spécifique, distinct de la simple désactivation d'une fiche.

Pour Teamworks, le module de frais existe déjà : Sentrifugo est donc plutôt un point de comparaison qu'une source de nouveau périmètre sur ce sujet.

## 7. Matrice des idées transférables

| Concept | Valeur pour Teamworks-CCNS | Décision de benchmark |
|---|---:|---|
| Historique RH daté / ligne de vie salarié | Très forte | À concevoir |
| Journal transactionnel des congés | Très forte | À concevoir |
| Workflow demande / validation absence | Très forte | À concevoir |
| Onboarding par checklist | Très forte | À concevoir |
| Offboarding par checklist | Très forte | À concevoir |
| Contacts d'urgence | Forte | À intégrer au dossier salarié |
| Diplômes / habilitations + dates d'expiration | Déjà stratégique | Consolider et brancher aux alertes |
| Export RGPD du dossier salarié | Forte | À prévoir |
| Purge / anonymisation RGPD | Forte | À prévoir avec politique de conservation |
| Journal d'audit des données RH sensibles | Forte | À consolider / généraliser |
| Promotions / transferts historisés | Forte | À rattacher à la ligne de vie RH |
| Dossier disciplinaire | Moyenne à forte | À étudier juridiquement et fonctionnellement |
| Performance / entretiens | Moyenne | À étudier ultérieurement |
| Gestion des actifs confiés | Faible à moyenne | Hors priorité tant que besoin non démontré |
| Helpdesk RH | Faible | Hors périmètre actuel |
| Badgeuse / biométrie | Faible | À écarter |
| Paie complète | Faible | À ne pas recréer sans décision explicite |
| Planning opérationnel métier | Nulle dans Teamworks | PMSL Équipe |
| Facturation / prestations | Nulle dans Teamworks | Noethys |

## 8. Lots fonctionnels candidats — sans identifiant TW à ce stade

Aucun identifiant `TW-*` n'est attribué ici afin de respecter la gouvernance de la roadmap.

### A. Dossier salarié enrichi
- identité ;
- administratif ;
- contacts d'urgence ;
- contrats / CCNS ;
- compétences, diplômes et habilitations ;
- absences ;
- historique ;
- documents ;
- données sensibles avec permissions adaptées.

### B. Historique RH / événements de carrière
- entrée ;
- nouveau contrat ;
- renouvellement ;
- changement de fonction ;
- changement de classification CCNS ;
- changement de temps contractuel ;
- changement d'affectation ;
- suspension éventuelle ;
- départ.

Principe : les événements historiques ne doivent pas être écrasés par l'état courant.

### C. Absences et congés
- types d'absence ;
- demande ;
- validation ;
- unités jour / demi-journée / heure ;
- journal des mouvements ;
- acquisition ;
- consommation ;
- report ;
- régularisation ;
- expiration ;
- solde calculé ;
- transmission des indisponibilités utiles à PMSL Équipe sans y déplacer la logique RH.

### D. Onboarding / offboarding
- modèles selon profil ;
- checklist ;
- responsable ;
- échéance ;
- statut ;
- relance ;
- documents à obtenir ;
- habilitations à vérifier ;
- actions de départ ;
- clôture contrôlée du dossier.

### E. RGPD et traçabilité
- export des données personnelles ;
- inventaire des données liées à un salarié ;
- règle de conservation par domaine ;
- anonymisation ;
- suppression des pièces lorsque licite ;
- journal d'accès / modification sur données sensibles ;
- permissions fines.

## 9. Principe d'utilisation de ce benchmark

Pour chaque nouveau dépôt inspecté :
1. identifier les fonctions réellement présentes dans le code ;
2. distinguer l'idée métier de son implémentation technique ;
3. comparer avec ce que Teamworks-CCNS sait déjà faire ;
4. écarter les fonctions hors périmètre ;
5. noter les idées réutilisables dans ce fichier ;
6. ne modifier la roadmap officielle qu'après arbitrage.

L'objectif n'est pas de transformer Teamworks en ERP RH universel, mais de sélectionner les fonctions qui rendent le cœur RH plus fiable, traçable et adapté aux besoins réels de PMSL et aux contraintes CCNS.