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

### Minimum légal CEE daté

Le coefficient légal n'est pas une constante intemporelle :

- du 1er mai 2008 au 30 avril 2025 : minimum journalier = `2,20 × SMIC horaire` ; la règle figurait d'abord à l'article D432-3 du CASF puis à D432-2 à partir de 2012 ;
- depuis le 1er mai 2025 : minimum journalier = `4,30 × SMIC horaire`, conformément à l'article D432-2 du CASF modifié par le décret n° 2024-1151 du 4 décembre 2024.

Le moteur résout donc d'abord le coefficient applicable à la date du contrat, puis la version du SMIC applicable à cette même date. Une date antérieure à l'historique réglementaire porté par Teamworks provoque une absence de règle explicite au lieu d'appliquer artificiellement le coefficient courant.

Toute l'arithmétique du calcul légal, multiplication comprise, est exécutée dans un contexte `Decimal` local. Le vieux runtime Teamworks peut laisser une précision globale très faible ; elle ne doit jamais transformer par exemple `12,31 × 4,30 = 52,933` en `53` avant l'arrondi au centime.

### Barèmes internes

Les barèmes employeur sont historisés par qualification et date d'effet dans une table dédiée. L'écran `Barèmes CEE…` permet de définir des montants différents pour BAFA titulaire, BAFA stagiaire, non diplômé, équivalence et BAFD.

Le logiciel compare le barème employeur au minimum légal CEE résolu à la date du contrat.

## Modèles de contrats et publipostage

Les fichiers de publipostage historiques restent disponibles sans métadonnées : l'absence de ciblage signifie « modèle legacy / secours ».

Un modèle peut désormais être ciblé explicitement :

- CCNS générique ;
- CCNS G1 à G8 ;
- CEE générique ;
- CEE BAFA titulaire, BAFA stagiaire, non diplômé, équivalence, BAFD titulaire ou BAFD stagiaire.

Le bouton d'impression d'un contrat ouvre un adaptateur dédié du publiposteur. Celui-ci filtre uniquement les modèles de la catégorie `contrat` et restaure immédiatement le sélecteur vanilla après construction du dialogue ; les autres usages du publiposteur ne sont donc pas modifiés.

Le ciblage se règle depuis le menu contextuel du fichier. Supprimer réellement un fichier supprime aussi sa métadonnée de ciblage afin qu'un futur fichier portant le même nom ne récupère pas une ancienne règle. Annuler la suppression ne modifie aucune métadonnée.

### Migration des anciens modèles CEE

Le modèle CEE livré historiquement avec Teamworks utilise des mots-clés et du texte qui précèdent TW-184. Il doit rester imprimable, mais une nouvelle version du modèle doit préférer les données du moteur moderne :

- `{BRUTJOUR}` est conservé comme **alias de compatibilité** de `{BAREMECEE}` pour un CEE moderne ; l'assistant ne demande donc plus une seconde saisie « salaire brut par jour » lorsque le barème CEE est déjà déterminé ;
- `{CLASSIFICATION}` est historique et reste vide sur un CEE moderne ; un modèle CEE mis à jour doit employer `{QUALIFICATIONCEE}` lorsqu'il veut afficher « BAFA titulaire », « BAFA stagiaire », etc. ;
- le minimum CEE ne doit jamais être écrit en dur dans le modèle. Employer `{MINIMUMCEE}` permet de reprendre le montant calculé à la date du contrat ;
- de même, une phrase figée comme « minimum = 2,2 heures de SMIC » est obsolète pour les contrats postérieurs au 30 avril 2025 et doit être remplacée par une formulation fondée sur `{MINIMUMCEE}` ou par une clause juridiquement maintenue dans le modèle.

L'écran de vérification du publipostage contrat adapte la largeur des libellés afin que les mots-clés longs TW-184 restent lisibles. Cette adaptation reste limitée à la catégorie `contrat`.

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
- nouvelles tables créées via l'adaptation historique de `GestionDB.CreationTable`, qui traduit notamment l'auto-incrément SQLite vers MySQL ;
- aucune migration automatique d'un ancien contrat vers CCNS ;
- source et date d'effet des grilles portées par le domaine ;
- journalisation détaillée des changements de contrat à compléter dans un incrément ultérieur.

## UX cible

Exemple CEE :

`Convention employeur` → `CEE` → `Qualification : BAFA stagiaire` → `Barème employeur` → `Minimum légal` → `Conformité`.

Exemple CDI CCNS :

`CCNS — Sport (IDCC 2511)` → `CDI` → `Groupe CCNS` → `Durée hebdomadaire` → `Brut mensuel` → `Minimum CCNS / SMIC` → `Conformité`.

## Tests

Le lot comporte des tests du domaine et de l'adaptateur CCNS ainsi qu'un smoke Windows du dialogue réel. Les contrôles couvrent notamment :

- présélection CCNS sur un nouveau contrat ;
- huit groupes G1 à G8 ;
- masquage de l'ancienne classification et de la valeur du point sur le parcours moderne ;
- contrôle de rémunération CCNS ;
- distinction BAFA titulaire / stagiaire et autres qualifications CEE ;
- bascule du minimum légal CEE `2,20 → 4,30` au 1er mai 2025 ;
- conservation du parcours des contrats historiques ;
- filtrage réel d'un modèle CCNS G1 contre un modèle G4 sous Windows ;
- conservation d'un modèle legacy non ciblé ;
- compatibilité `{BRUTJOUR}` des anciens modèles CEE sans double saisie utilisateur.

## Hors périmètre immédiat

- génération juridique exhaustive de toutes les clauses du contrat ;
- prise en charge complète d'ÉCLAT ou des centres sociaux ;
- migration automatique des anciens contrats ;
- moteur définitif de période d'essai par convention ;
- contrôle mensuel artificiel des minima annuels G7/G8.
