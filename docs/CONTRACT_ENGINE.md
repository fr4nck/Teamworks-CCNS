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

## État d'implémentation du premier incrément

Le premier incrément TW-184 est désormais raccordé à l'assistant wx historique :

- `convention_code` est stocké séparément sur le contrat ;
- `ccns_group` stocke G1 à G8 sans détourner `IDclassification` ;
- `weekly_hours` et `gross_monthly_salary` deviennent des données standard du contrat ;
- `cee_qualification` stocke le statut CEE ;
- toutes ces colonnes sont additives, nullable et créées de façon idempotente, sans `ADD COLUMN IF NOT EXISTS` afin de préserver MySQL/MariaDB 5.5 ;
- un nouveau contrat Teamworks-CCNS propose CCNS par défaut ;
- un contrat historique sans `convention_code` n'est jamais converti implicitement ;
- le parcours historique `IDclassification + valeur_point` reste disponible uniquement comme fallback des anciennes données ou des conventions non encore raccordées.

## CCNS — contrats classiques

Pour les CDI/CDD relevant pleinement de la Convention collective nationale du sport :

- utiliser les groupes CCNS G1 à G8 issus du moteur de grille existant ;
- proposer les minima applicables à la date du contrat ;
- contrôler le minimum conventionnel et le SMIC ;
- appliquer le calcul temps partiel déjà porté par le domaine ;
- stocker durée hebdomadaire et rémunération indépendamment des champs personnalisés ;
- ne plus utiliser une « valeur du point » générique comme pivot ;
- calculer ou proposer la période d'essai uniquement si elle est juridiquement permise et pertinente pour le contrat.

### Contrôle de rémunération

Pour G1 à G6, l'assistant affiche :

`Minimum CCNS` → `Minimum SMIC` → `Minimum retenu` → `Conforme / non conforme`.

Le minimum retenu est le montant le plus favorable au salarié selon le moteur existant. Une rémunération inférieure au minimum calculé empêche la validation du contrat.

G7 et G8 ont des minima annuels. L'assistant les identifie comme tels et n'effectue volontairement aucune conversion mensuelle artificielle.

## CEE — régime spécifique

Le contrat d'engagement éducatif ne doit pas être assimilé à une classification CCNS classique.

Quand `Type de contrat = CEE`, le parcours devient :

- qualification / statut :
  - BAFA titulaire ;
  - BAFA stagiaire ;
  - non diplômé ;
  - équivalence / qualification reconnue ;
  - BAFD titulaire ;
  - BAFD stagiaire ;
- barème journalier interne de l'employeur ;
- contrôle du minimum légal CEE applicable à la date ;
- dates du contrat ;
- à terme : fonction, compteur annuel de jours CEE et règles spécifiques mineurs.

Un nouveau CEE ne renseigne ni classification CCNS ni ancienne valeur du point. Un CEE historique sans qualification moderne reste lisible et modifiable sans conversion forcée.

### Barèmes internes

Les barèmes employeur sont historisés par qualification et date d'effet dans une table dédiée. L'écran `Barèmes CEE…` permet de définir des montants différents pour BAFA titulaire, BAFA stagiaire, non diplômé, équivalence et BAFD.

Le logiciel compare le barème employeur au minimum légal CEE résolu à la date du contrat.

## Autres conventions

L'architecture ne code pas la CCNS comme unique convention possible. Les codes actuellement prévus sont :

- `CCNS` ;
- `ECLAT` ;
- `CENTRES_SOCIAUX` ;
- `OTHER`.

ÉCLAT et Centres sociaux sont reconnus par l'assistant mais leur moteur détaillé n'est pas encore raccordé. Dans ce cas, Teamworks affiche explicitement que le parcours historique est conservé sans prétendre effectuer un contrôle conventionnel.

Chaque futur moteur pourra définir classifications, minima, période d'essai, ancienneté, temps de travail, primes et règles de contrôle propres.

## Données et compatibilité

- aucune migration destructive de la base MySQL/MariaDB 5.5 ;
- préserver la lecture des contrats historiques ;
- conserver les anciennes valeurs lorsqu'elles existent ;
- nouvelles colonnes nullable et additives ;
- aucune migration automatique d'un ancien contrat vers CCNS ;
- source et date d'effet des grilles portées par le domaine ;
- journalisation détaillée des changements de contrat à compléter dans un incrément ultérieur.

## UX cible

Exemple CEE :

`Convention employeur` → `CEE` → `Qualification : BAFA stagiaire` → `Barème employeur` → `Minimum légal` → `Conformité`.

Exemple CDI CCNS :

`CCNS — Sport (IDCC 2511)` → `CDI` → `Groupe CCNS` → `Durée hebdomadaire` → `Brut mensuel` → `Minimum CCNS / SMIC` → `Conformité`.

## Tests

Le lot comporte des tests du domaine et de l'adaptateur CCNS ainsi qu'un smoke Windows du dialogue réel. Le smoke vérifie notamment qu'un nouveau contrat :

- présélectionne CCNS ;
- expose les huit groupes G1 à G8 ;
- masque l'ancienne classification et la valeur du point ;
- affiche le bloc de contrôle CCNS ;
- conserve le parcours des contrats historiques.

## Hors périmètre immédiat

- génération juridique exhaustive de toutes les clauses du contrat ;
- prise en charge complète d'ÉCLAT ou des centres sociaux ;
- migration automatique des anciens contrats ;
- moteur définitif de période d'essai par convention ;
- contrôle mensuel artificiel des minima annuels G7/G8.
