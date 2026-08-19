# TW-184 — Moteur de contrats piloté par convention

## Objectif

Remplacer le parcours générique hérité de Noethys par un moteur de création de contrat piloté par la convention collective, le type de contrat et le statut/qualification du salarié.

Le moteur doit empêcher les mélanges entre :

- classification conventionnelle ;
- type de contrat ;
- qualification professionnelle ;
- statut particulier ;
- barème interne de rémunération ;
- minimum légal ou conventionnel.

## Principe de saisie

Ordre cible :

1. convention applicable ;
2. type de contrat ;
3. fonction / métier ;
4. classification conventionnelle si elle s'applique ;
5. qualification ou statut spécifique si nécessaire ;
6. durée / dates / temps de travail ;
7. rémunération proposée ;
8. contrôles automatiques et avertissements.

Les champs doivent être contextuels : un champ sans sens pour le contrat choisi ne doit pas être affiché comme s'il était obligatoire.

## CCNS — contrats classiques

Pour les CDI/CDD relevant pleinement de la Convention collective nationale du sport :

- utiliser les groupes et classifications CCNS ;
- proposer les minima applicables à la date du contrat ;
- contrôler le minimum conventionnel et le SMIC ;
- distinguer salaire de base, éventuels compléments et temps de travail ;
- ne plus utiliser une « valeur du point » générique comme pivot si elle ne correspond pas au mécanisme conventionnel en vigueur ;
- calculer ou proposer la période d'essai uniquement si elle est juridiquement permise et pertinente pour le contrat.

## CEE — régime spécifique

Le contrat d'engagement éducatif ne doit pas être assimilé à une classification CCNS classique.

Quand `Type de contrat = CEE`, le parcours devient :

- fonction : animateur, directeur, adjoint ou autre fonction autorisée ;
- qualification / statut :
  - BAFA titulaire ;
  - BAFA stagiaire ;
  - non diplômé ;
  - équivalence / qualification reconnue ;
  - BAFD titulaire ou stagiaire lorsqu'il s'agit de direction ;
- barème journalier interne de l'employeur ;
- contrôle du minimum légal CEE applicable à la date ;
- nombre de jours / période ;
- compteur annuel de jours CEE et alertes associées ;
- règles spécifiques mineurs si le salarié est mineur.

### Barèmes internes

Teamworks doit permettre à chaque organisation de définir ses propres barèmes CEE par fonction et qualification.

Exemple de structure de barème :

| Fonction | Qualification | Montant journalier | Date d'effet |
|---|---|---:|---|
| Animateur | BAFA titulaire | configurable | configurable |
| Animateur | BAFA stagiaire | configurable | configurable |
| Animateur | Non diplômé | configurable | configurable |
| Directeur | BAFD titulaire | configurable | configurable |
| Directeur | BAFD stagiaire | configurable | configurable |

Le logiciel doit proposer le barème configuré mais laisser une modification explicite si l'utilisateur dispose des droits nécessaires, tout en conservant le contrôle du minimum légal.

## Autres conventions

L'architecture ne doit pas coder en dur la CCNS dans l'interface.

Elle doit permettre ultérieurement d'ajouter des moteurs de règles pour :

- ÉCLAT ;
- acteurs du lien social et familial / centres sociaux ;
- autres conventions ou accords applicables à une organisation.

Chaque convention peut définir :

- classifications ;
- minima ;
- règles de période d'essai ;
- contrats spécifiques ;
- ancienneté ;
- temps de travail ;
- primes et sujétions ;
- règles de contrôle propres.

## Données et compatibilité

- aucune migration destructive de la base MySQL/MariaDB 5.5 ;
- préserver la lecture des contrats historiques ;
- conserver les anciennes valeurs lorsqu'elles existent, même si elles sont désormais considérées comme « héritées » ;
- introduire les nouveaux champs progressivement avec fallback ;
- journaliser les changements de classification, barème et rémunération ;
- afficher la source et la date d'effet d'une règle lorsque cela est possible.

## UX cible

L'assistant ne doit plus présenter simultanément des listes incohérentes.

Exemple CEE :

`Convention / régime : CEE` → `Fonction : Animateur` → `Qualification : BAFA stagiaire` → `Barème employeur` → `Contrôle minimum légal`.

Exemple CDI CCNS :

`Convention : Sport` → `CDI` → `Métier` → `Groupe CCNS` → `Minimum conventionnel` → `Rémunération` → `Temps de travail` → `Période d'essai applicable`.

## Tests attendus

- CEE BAFA titulaire et stagiaire produisent des propositions de rémunération distinctes lorsque les barèmes employeur sont distincts ;
- le minimum légal CEE est toujours contrôlé ;
- un CEE n'expose pas une pseudo-classification CCNS ;
- un CDI/CDD CCNS propose uniquement les classifications CCNS compatibles ;
- les contrats historiques restent ouvrables ;
- les règles sont sélectionnées selon la date d'effet ;
- les erreurs de combinaison convention/contrat/statut sont bloquées ou clairement signalées ;
- aucun changement de schéma destructif n'est requis.

## Hors périmètre immédiat

- génération juridique exhaustive de toutes les clauses du contrat ;
- prise en charge complète d'ÉCLAT ou des centres sociaux dès le premier lot ;
- migration automatique des anciens contrats vers une nouvelle classification.

Le premier incrément doit sécuriser le modèle et le parcours CCNS/CEE avant d'étendre les autres conventions.
