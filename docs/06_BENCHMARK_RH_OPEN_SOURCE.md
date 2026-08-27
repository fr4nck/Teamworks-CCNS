# Étude comparative RH libre — idées transférables à Teamworks-CCNS

**Statut : document vivant**  
**Créé : 27 août 2026**

> Ce document n'est pas une feuille de route concurrente de `ROADMAP.md`. Il sert de mémoire de recherche et de source d'idées. Toute intégration réelle devra être arbitrée puis inscrite séparément dans la feuille de route officielle.

## 1. Garde-fou de périmètre

Teamworks-CCNS reste un outil **RH** : salariés, contrats, temps de travail, compétences et diplômes, absences, obligations employeur, contraintes CCNS et données administratives RH.

Il ne doit pas absorber :
- la facturation ou les prestations métier ;
- la gestion d'activités ALSH ou sportives ;
- le planning opérationnel des séances ;
- la recherche de remplaçants opérationnels ;
- les fonctions métier relevant de Noethys ou de PMSL Équipe.

L'étude comparative vise donc uniquement des fonctions RH transférables sans brouiller cette séparation.

## 2. Première passe — petits projets RH inspectés

Dépôts exploratoires déjà étudiés : `staff-manager`, `humanresource`, `HRMS`, `Employee-Attendance-Management`.

Enseignements retenus :
- dossier salarié structuré par sous-domaines ;
- contacts d'urgence ;
- historique d'emploi daté ;
- circuit de demande et de validation des congés avec plusieurs états ;
- compteurs par type d'absence ;
- absences possibles en heures ou fractions de journée ;
- archivage plutôt que suppression brutale ;
- organisation par services et fonctions ;
- recherche et actions RH en masse.

Les idées les plus fortes de cette première passe sont :
1. une **ligne de vie RH** historisée ;
2. un **moteur d'absences et congés** avec mouvements de compteur ;
3. un **dossier salarié enrichi** ;
4. un **tableau de bord des échéances RH**.

## 3. OrangeHRM — dossier salarié composable et RGPD

Dépôt : `orangehrm/orangehrm` — OrangeHRM Starter, GPL.

### Concepts observés

OrangeHRM découpe le dossier du salarié en entités dédiées :
- contact d'urgence ;
- personnes à charge ;
- expérience professionnelle ;
- formation ;
- compétences ;
- langues ;
- licences et habilitations avec dates ;
- adhésions ;
- rémunération ;
- rattachements et localisation ;
- contrat ;
- hiérarchie ;
- évaluations ;
- congés ;
- présence.

Cette structure confirme qu'une fiche salarié robuste gagne à être **composée de sous-dossiers spécialisés** plutôt qu'à devenir un formulaire unique surchargé.

### Idée particulièrement importante : RGPD intégré au logiciel de gestion RH

OrangeHRM possède des mécanismes explicites :
- d'**accès et d'export** des données d'un salarié ;
- de **purge et d'anonymisation** des données personnelles, champ par champ et entité par entité.

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

## 4. Frappe HR — cycle de vie salarié et journal des droits à congés

Dépôt : `frappe/hrms` — solution RH libre moderne.

### Cycle de vie salarié

Frappe HR traite explicitement :
- recrutement ;
- offre d'emploi ;
- parcours d'intégration à l'arrivée ;
- dossier salarié ;
- promotions ;
- changements d'affectation ;
- préparation du départ ;
- entretien de départ.

Il existe donc un véritable **cycle de vie RH**, et non une simple fiche dont les valeurs courantes écrasent les précédentes.

### Arrivée et départ sous forme de parcours organisé

Le parcours d'intégration contient :
- un modèle réutilisable ;
- une liste d'actions ;
- une date de début ;
- une durée ;
- un responsable désigné par utilisateur ou rôle ;
- des tâches générées automatiquement ;
- des échéances ajustées en fonction des jours non travaillés ;
- un état `À faire / En cours / Terminé` ;
- la possibilité de notifier les responsables.

Le même principe est utilisé pour organiser le départ du salarié.

### Journal des droits à congés

Frappe HR possède un journal dans lequel chaque mouvement rattache :
- un salarié ;
- un type de congé ;
- une origine de mouvement ;
- une quantité ;
- une période ;
- un éventuel report ;
- une expiration ;
- le caractère sans solde.

Cette architecture valide fortement l'idée de **calculer un solde à partir d'un journal de mouvements** plutôt que de stocker un nombre modifiable sans traçabilité.

### Transposition Teamworks-CCNS

À retenir :
- liste de contrôle d'arrivée ;
- liste de contrôle de départ ;
- responsable et échéance pour chaque action RH ;
- modèles selon le type de salarié ou de contrat ;
- historique des promotions et changements d'affectation ;
- journal transactionnel des droits à absence.

**Priorité conceptuelle : très élevée.**

## 5. Horilla HRMS — discipline, audit et processus RH plus larges

Dépôt : `horilla/horilla-hr` — LGPL, branche 2.0 active.

### Fonctions visibles

Horilla couvre notamment :
- gestion des salariés ;
- recrutement complet ;
- parcours d'arrivée et de départ ;
- présence et temps de travail ;
- congés ;
- paie ;
- suivi des objectifs et évaluations ;
- matériels confiés ;
- assistance RH ;
- journalisation et audit ;
- actions disciplinaires.

Le dépôt contient un véritable domaine consacré aux **actions disciplinaires**, avec types d'action, formulaires, listes, filtres et dossiers associés.

### Transposition Teamworks-CCNS

À retenir avec prudence :
- **journal d'audit** des modifications RH sensibles ;
- **dossier disciplinaire** séparé du dossier courant du salarié ;
- dates, nature de l'action, documents et historique ;
- droits d'accès renforcés ;
- meilleure continuité entre recrutement, arrivée et dossier salarié.

À ne pas reprendre automatiquement :
- assistance interne généraliste ;
- badgeuse ou biométrie ;
- paie complète ;
- gestion générale du matériel, sauf besoin RH démontré.

**Priorité : audit élevé ; discipline à évaluer fonctionnellement et juridiquement.**

## 6. Sentrifugo — modules séparés et gestion de sortie

Dépôt : `Sentrifugo/sentrifugo`.

Projet plus ancien, mais intéressant comme référence fonctionnelle. Son architecture sépare notamment des modules consacrés :
- au matériel confié (`assets`) ;
- au départ du salarié (`exit`) ;
- aux frais (`expenses`) ;
- à la gestion du temps (`timemanagement`).

L'intérêt n'est pas technologique, mais métier : un **départ salarié** mérite un domaine spécifique, distinct de la simple désactivation d'une fiche.

Pour Teamworks, le module de frais existe déjà : Sentrifugo est donc plutôt un point de comparaison qu'une source de nouveau périmètre sur ce sujet.

## 7. Odoo RH — versions datées de la situation du salarié

Dépôt : `odoo/odoo`, module `hr` de la version 19.

### Une découverte particulièrement pertinente pour Teamworks

Odoo possède désormais un objet `hr.version` qui conserve des **versions datées de la situation d'un salarié**.

Une version peut regrouper notamment :
- la date d'effet ;
- la fonction ;
- le service ;
- le lieu de travail ;
- le temps de travail ;
- le type de contrat ;
- le début et la fin du contrat ;
- la fin de période d'essai ;
- la rémunération ;
- le responsable RH ;
- la date et le motif de départ ;
- l'auteur et la date de la dernière modification.

Odoo interdit par ailleurs plusieurs versions actives partageant la même date d'effet pour un même salarié.

Cela confirme très directement notre idée de **ligne de vie RH** : au lieu d'écraser l'ancienne situation lorsque le contrat, la fonction, la classification ou le temps de travail change, on crée un nouvel état daté.

### Séparation des informations publiques et privées

Odoo expose également une vue `hr.employee.public` qui ne contient que les informations que les autres utilisateurs peuvent consulter : identité professionnelle, fonction, service, coordonnées professionnelles, responsable, lieu de travail, etc.

Les informations privées restent dans le domaine RH protégé.

### Transposition Teamworks-CCNS

Deux idées sont particulièrement fortes :

1. **Versionner la situation RH du salarié par date d'effet** : contrat, temps de travail, fonction, classification CCNS, groupe, rémunération, affectation et statut.
2. **Distinguer explicitement les données RH sensibles des informations professionnelles ordinaires**, plutôt que de gérer les droits seulement écran par écran.

**Priorité conceptuelle : très élevée.**

## 8. Matrice des idées transférables

| Concept | Valeur pour Teamworks-CCNS | Décision issue de l'étude |
|---|---:|---|
| Historique RH daté / ligne de vie salarié | Très forte | À concevoir |
| Versions de situation avec date d'effet | Très forte | À concevoir |
| Journal transactionnel des congés | Très forte | À concevoir |
| Circuit de demande et validation des absences | Très forte | À concevoir |
| Parcours d'intégration à l'arrivée | Très forte | À concevoir |
| Parcours organisé de départ | Très forte | À concevoir |
| Contacts d'urgence | Forte | À intégrer au dossier salarié |
| Diplômes / habilitations + dates d'expiration | Déjà stratégique | Consolider et brancher aux alertes |
| Séparation données professionnelles / données RH sensibles | Très forte | À concevoir |
| Export RGPD du dossier salarié | Forte | À prévoir |
| Purge / anonymisation RGPD | Forte | À prévoir avec politique de conservation |
| Journal d'audit des données RH sensibles | Forte | À consolider / généraliser |
| Promotions / changements d'affectation historisés | Forte | À rattacher à la ligne de vie RH |
| Dossier disciplinaire | Moyenne à forte | À étudier juridiquement et fonctionnellement |
| Entretiens et évaluations | Moyenne | À étudier ultérieurement |
| Gestion des matériels confiés | Faible à moyenne | Hors priorité tant que besoin non démontré |
| Assistance interne RH | Faible | Hors périmètre actuel |
| Badgeuse / biométrie | Faible | À écarter |
| Paie complète | Faible | À ne pas recréer sans décision explicite |
| Planning opérationnel métier | Nulle dans Teamworks | PMSL Équipe |
| Facturation / prestations | Nulle dans Teamworks | Noethys |

## 9. Lots fonctionnels candidats — sans identifiant TW à ce stade

Aucun identifiant `TW-*` n'est attribué ici afin de respecter la gouvernance de la feuille de route.

### A. Dossier salarié enrichi
- identité ;
- administratif ;
- contacts d'urgence ;
- contrats et CCNS ;
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

### D. Parcours d'arrivée et de départ
- modèles selon profil ;
- liste de contrôle ;
- responsable ;
- échéance ;
- état d'avancement ;
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
- journal d'accès et de modification sur les données sensibles ;
- permissions fines.

## 10. Principe d'utilisation de cette étude

Pour chaque nouveau dépôt inspecté :
1. identifier les fonctions réellement présentes dans le code ;
2. distinguer l'idée métier de son implémentation technique ;
3. comparer avec ce que Teamworks-CCNS sait déjà faire ;
4. écarter les fonctions hors périmètre ;
5. noter les idées réutilisables dans ce fichier ;
6. ne modifier la feuille de route officielle qu'après arbitrage.

L'objectif n'est pas de transformer Teamworks en progiciel RH universel, mais de sélectionner les fonctions qui rendent le cœur RH plus fiable, traçable et adapté aux besoins réels de PMSL et aux contraintes CCNS.