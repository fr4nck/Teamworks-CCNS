# TW-184 — Moteur de contrats piloté par convention

## Objectif

Remplacer le parcours générique hérité de Noethys par un moteur de création de contrat piloté par la convention collective, le type de contrat, la nature de l'opération et le statut/qualification du salarié.

Le moteur doit empêcher les mélanges entre :

- classification conventionnelle ;
- type de contrat ;
- nature de l'opération contractuelle ;
- qualification professionnelle ;
- statut particulier ;
- barème interne de rémunération ;
- minimum légal ou conventionnel ;
- période d'essai et ancienneté.

## Principe de saisie

Ordre cible :

1. convention applicable ;
2. nature de l'opération : nouveau contrat, renouvellement CDD ou passage CDD → CDI ;
3. type de contrat ;
4. contrat précédent lorsqu'une continuité doit être établie ;
5. fonction / métier ;
6. classification conventionnelle si elle s'applique ;
7. qualification ou statut spécifique si nécessaire ;
8. durée / dates / temps de travail ;
9. rémunération proposée ;
10. période d'essai proposée lorsqu'elle est applicable ;
11. contrôles automatiques et avertissements.

Les champs sont contextuels : un champ sans sens pour le contrat choisi ne doit pas être affiché comme s'il était obligatoire.

## État d'implémentation de TW-184

TW-184 est raccordé à l'assistant wx historique :

- `convention_code` est stocké séparément sur le contrat ;
- `ccns_group` stocke G1 à G8 sans détourner `IDclassification` ;
- `weekly_hours`, `gross_monthly_salary` et `gross_annual_salary` deviennent des données standard du contrat ;
- `cee_qualification` stocke le statut CEE ;
- `operation_type` distingue `NEW`, `CDD_RENEWAL` et `CDD_TO_CDI` ;
- `previous_contract_id` rattache un renouvellement ou une poursuite en CDI au CDD précédent ;
- `trial_period_value` et `trial_period_unit` stockent la période d'essai sous forme structurée ;
- le champ historique `essai` continue d'être alimenté en jours calendaires pour préserver les anciens modèles et anciennes fonctions ;
- toutes ces colonnes sont additives, nullable et créées de façon idempotente, sans `ADD COLUMN IF NOT EXISTS` afin de préserver MySQL/MariaDB 5.5 ;
- un nouveau contrat Teamworks-CCNS propose CCNS et l'opération `Nouveau contrat` par défaut ;
- un contrat historique sans les nouveaux discriminants n'est jamais converti implicitement ;
- le parcours historique `IDclassification + valeur_point` reste disponible uniquement comme fallback des anciennes données ou des conventions non encore raccordées.

## Nature de l'opération et continuité contractuelle

Le type du contrat ne suffit pas à déterminer les règles applicables. L'assistant distingue donc explicitement :

- **Nouveau contrat** ;
- **Renouvellement d'un CDD** ;
- **Passage CDD → CDI**.

Pour un renouvellement ou un passage CDD → CDI, Teamworks demande le CDD précédent et vérifie que le nouveau contrat commence immédiatement après sa date de fin.

Cette relation est stockée par `previous_contract_id`. Elle permettra également d'alimenter progressivement les futurs contrôles d'ancienneté et de continuité sans tenter de déduire ces situations à partir de simples ressemblances de dates.

## Période d'essai

La période d'essai devient une donnée métier calculée et non plus un simple nombre de jours libre.

L'assistant affiche :

- une case `Prévoir une période d'essai` ;
- une durée ;
- une unité `jour(s) calendaires` ou `mois calendaires` ;
- l'explication de la proposition automatique.

La période d'essai reste facultative lorsqu'elle est juridiquement possible : Teamworks propose le maximum applicable mais l'utilisateur peut la réduire ou la supprimer. Une durée supérieure au maximum calculé est refusée.

### Nouveau CDI CCNS

La proposition maximale est calculée selon la catégorie correspondant au groupe :

- G1-G2 : 1 mois ;
- G3-G5 : 2 mois ;
- G6-G8 : 3 mois.

Les mois sont conservés comme mois calendaires. Le champ historique `essai`, qui exige un entier en jours, est alimenté à partir de la vraie date de début : un mois de février n'est donc jamais transformé artificiellement en 30 jours.

### Nouveau CDD

Lorsque le terme du CDD est connu, le moteur propose la période d'essai à partir de la durée du contrat et applique les plafonds du régime CDD :

- un jour par semaine de contrat dans la limite de deux semaines lorsque le CDD est de six mois au plus ;
- un mois au maximum lorsque le CDD dépasse six mois.

L'implémentation courante compte une semaine commencée comme une semaine pour produire la proposition automatique. Ce détail de calcul devra rester vérifié contre la source juridique applicable avant d'être considéré comme une règle conventionnelle autonome de Teamworks.

Si la durée permettant le calcul n'est pas disponible, Teamworks n'invente pas de valeur et laisse le cas explicite.

### Renouvellement CDD

Un renouvellement de CDD ne crée **aucune nouvelle période d'essai**.

L'opération `CDD_RENEWAL` force donc une proposition de zéro et évite l'ancien avertissement Teamworks qui assimilait systématiquement zéro à une saisie oubliée.

### Passage CDD → CDI

Pour `CDD_TO_CDI`, Teamworks :

1. sélectionne le CDD précédent ;
2. vérifie la continuité des dates ;
3. calcule la période d'essai CDI théorique à partir du groupe CCNS ;
4. déduit la durée du CDD précédent ;
5. ramène le résultat à zéro lorsque le CDD précédent absorbe toute la période d'essai théorique.

Le calcul est conservateur : il s'appuie sur le contrat explicitement relié, plutôt que de sommer automatiquement tous les anciens CDD de la personne malgré d'éventuelles interruptions ou changements de situation.

### CEE

Le CEE n'utilise pas le moteur de période d'essai CDI/CDD et la proposition est nulle.

## CCNS — contrats classiques

Pour les CDI/CDD relevant pleinement de la Convention collective nationale du sport :

- utiliser les groupes CCNS G1 à G8 issus du moteur de grille existant ;
- proposer les minima applicables à la date du contrat ;
- contrôler le minimum conventionnel et le SMIC ;
- appliquer le calcul temps partiel déjà porté par le domaine pour les minima mensuels ;
- stocker durée hebdomadaire et rémunération indépendamment des champs personnalisés ;
- ne plus utiliser une « valeur du point » générique comme pivot ;
- proposer automatiquement la période d'essai lorsque le parcours le permet.

### Contrôle de rémunération — G1 à G6

Pour G1 à G6, l'assistant calcule :

`Minimum CCNS` → `Minimum SMIC` → `Minimum retenu` → `Conforme / non conforme`.

Le minimum retenu est le montant le plus favorable au salarié selon le moteur existant. Lorsque l'utilisateur choisit un groupe, la case de rémunération est **préremplie directement avec ce minimum retenu** si elle est vide ou contient encore une valeur précédemment préremplie.

Une valeur saisie manuellement n'est jamais écrasée par un changement de rafraîchissement. Une rémunération inférieure au minimum calculé empêche la validation du contrat.

### G7 et G8 — minimum annuel

G7 et G8 ont des minima annuels. Teamworks ne fabrique donc plus de faux minimum mensuel.

Lorsqu'un groupe G7 ou G8 est choisi :

- le libellé devient `Rémunération annuelle de référence` ;
- l'unité devient `€ brut / an` ;
- la case est préremplie avec le minimum annuel CCNS applicable à la date ;
- l'écran rappelle que, pour une période incomplète, le minimum conventionnel est apprécié au prorata du nombre de mois concernés ;
- à temps plein, une référence annuelle inférieure au minimum de groupe est refusée avant écriture.

Le calcul complet d'un minimum annuel temps partiel et de la rémunération réellement due sur une période incomplète reste distinct de cette valeur annuelle de référence et devra être traité dans un incrément spécialisé.

## Ancienneté et expérience professionnelle

TW-184 ne transforme pas encore l'ancienneté en moteur automatique de prime.

Le modèle cible distingue explicitement :

- **ancienneté reconnue chez l'employeur**, qui pourra être alimentée par la continuité des contrats et des ajustements explicites ;
- **expérience professionnelle extérieure**, qui peut justifier une rémunération supérieure mais ne doit pas être confondue automatiquement avec l'ancienneté acquise dans l'entreprise.

La relation `previous_contract_id` constitue le premier socle fiable pour calculer ultérieurement la continuité CDD → CDI et les renouvellements sans sommer aveuglément toutes les anciennes périodes de la personne.

Le futur moteur d'ancienneté CCNS devra couvrir les groupes 1 à 6 et rester séparé du minimum salarial de base.

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

- du 1er mai 2008 au 30 avril 2025 : minimum journalier = `2,20 × SMIC horaire` ;
- depuis le 1er mai 2025 : minimum journalier = `4,30 × SMIC horaire`.

Le moteur résout d'abord le coefficient applicable à la date du contrat, puis la version du SMIC applicable à cette même date. Une date antérieure à l'historique réglementaire porté par Teamworks provoque une absence de règle explicite au lieu d'appliquer artificiellement le coefficient courant.

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
- une phrase figée comme « minimum = 2,2 heures de SMIC » est obsolète pour les contrats postérieurs au 30 avril 2025 et doit être remplacée par une formulation fondée sur `{MINIMUMCEE}` ou par une clause juridiquement maintenue dans le modèle.

L'écran de vérification du publipostage contrat adapte la largeur des libellés afin que les mots-clés longs TW-184 restent lisibles. Cette adaptation reste limitée à la catégorie `contrat`.

Le champ historique `{ESSAI}` reste disponible en jours pour les anciens modèles. Des mots-clés documentaires dédiés à la nature de l'opération, à la période d'essai structurée et à la rémunération annuelle pourront être ajoutés sans modifier la compatibilité de `{ESSAI}`.

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

`Nouveau contrat` → `Convention employeur` → `CEE` → `Qualification : BAFA stagiaire` → `Barème employeur` → `Minimum légal` → `Conformité`.

Exemple nouveau CDI CCNS :

`Nouveau contrat` → `CCNS — Sport (IDCC 2511)` → `CDI` → `Groupe CCNS` → `Durée hebdomadaire` → `Minimum prérempli` → `Période d'essai proposée` → `Conformité`.

Exemple renouvellement :

`Renouvellement d'un CDD` → `CDD précédent` → `CDD` → `continuité des dates` → `aucune nouvelle période d'essai`.

Exemple poursuite en CDI :

`Passage CDD → CDI` → `CDD précédent` → `CDI` → `Groupe CCNS` → `période CDI théorique - durée du CDD précédent`.

## Tests

Le lot comporte des tests du domaine, des garde-fous statiques et des smokes Windows du dialogue réel. Les contrôles couvrent notamment :

- présélection CCNS sur un nouveau contrat ;
- huit groupes G1 à G8 ;
- minimum mensuel CCNS/SMIC et conformité ;
- proposition d'essai CDI G1/G4/G7 ;
- calcul de période d'essai CDD et plafonds ;
- renouvellement CDD avec zéro nouvelle période d'essai ;
- déduction du CDD précédent lors du passage en CDI ;
- conversion exacte des mois calendaires vers le champ legacy en jours ;
- masquage permanent des anciens contrôles d'essai après rafraîchissement wx ;
- rémunération annuelle de référence pour G7/G8 ;
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
- moteur complet de prime d'ancienneté CCNS ;
- reconnaissance automatique de l'expérience professionnelle acquise chez d'autres employeurs comme ancienneté entreprise ;
- calcul annuel temps partiel complet G7/G8 et calcul de rémunération due sur une période incomplète ;
- reconstruction automatique d'une chaîne complexe de plusieurs CDD séparés sans relation explicite.
