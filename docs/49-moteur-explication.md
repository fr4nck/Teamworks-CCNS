# Préparation du moteur d'explication CCNS

## Statut du document

Ce document est un audit préparatoire. Il ne décrit aucun changement de règle métier, aucun changement de calcul et aucune modification de salaire. Son rôle est d'identifier ce que les objets `CalculationResult` et `Anomaly` permettent déjà d'expliquer, ce qui manque encore, et les points de branchement possibles pour un futur moteur d'explication.

## Périmètre observé

L'audit porte sur :

- les modèles `domain.engine.calculation_result.CalculationResult` et `domain.engine.anomaly.Anomaly` ;
- les contrôles qui produisent ces objets dans `domain/engine` ;
- les services de restitution `application/control` ;
- les dépôts en mémoire associés dans `infrastructure/repositories/engine_repository.py` ;
- les tests existants qui figent certains usages.

## Aujourd'hui

### `CalculationResult`

`CalculationResult` représente la trace structurée d'un contrôle ou d'un calcul. Les champs actuellement disponibles sont les suivants.

| Champ | Rôle actuel | Usage observé |
| --- | --- | --- |
| `id`, `created_at`, `updated_at` | Identité technique héritée de `Entity`. | Utilisé implicitement, notamment par `Anomaly.calculation_result_id`. |
| `object_type` | Type d'objet contrôlé (`contract`, `assignment`, etc.). | Obligatoire ; utilisé pour trier les lignes du tableau de contrôle. |
| `object_id` | Identifiant de l'objet contrôlé. | Obligatoire ; utilisé pour trier et afficher les anomalies reliées. |
| `person_id` | Identifiant de la personne concernée. | Alimenté par la plupart des contrôles ; restitué dans les vues et lignes de contrôle. |
| `contract_id` | Identifiant du contrat concerné. | Très utilisé pour filtrer les résultats contrat. |
| `assignment_id` | Identifiant de l'affectation concernée. | Utilisé pour filtrer les résultats affectation. |
| `rule_id` | Identifiant d'une règle persistée. | Rarement ou pas alimenté dans les contrôles actuels. |
| `rule_code` | Code métier du contrôle. | Très utilisé comme identifiant lisible de règle ; sert aussi de message de repli. |
| `rule_reference_code` | Code de référence réglementaire. | Alimenté pour certains contrôles documentés : minimum de grille et ancienneté. |
| `legal_certainty` | Niveau de certitude juridique associé au résultat. | Alimenté pour les contrôles raccordés à une référence ; utile pour l'explication mais encore peu restitué. |
| `calculation_date` | Date de calcul ou date de référence. | Alimentée par les contrôles, soit avec `date.today()`, soit avec une date de référence explicite. |
| `retained_base` | Base retenue pour le calcul ou la comparaison. | Alimentée pour les contrôles quantitatifs, avec des conventions hétérogènes (`smc_group_3`, type de minimum, heures, groupe...). |
| `actual_value` | Valeur observée ou saisie. | Très utile pour les comparaisons, mais son sens varie selon le contrôle. |
| `theoretical_value` | Valeur attendue ou seuil théorique. | Très utile pour les minima, l'ancienneté, les seuils et barèmes. |
| `retained_coefficient` | Coefficient appliqué ou retenu. | Alimenté par certains contrôles ; absent pour l'ancienneté montant alors que le taux est placé dans `details`. |
| `gap` | Écart entre valeur observée et valeur attendue. | Alimenté pour plusieurs contrôles, mais le signe n'a pas une signification uniforme dans tous les domaines. |
| `status` | Statut synthétique du résultat. | Utilisé dans les tests et disponible pour les vues, mais les écrans actuels exposent surtout les messages. |
| `readable_message` | Message utilisateur court. | Très utilisé dans les vues contrat et affectation. |
| `details` | Complément libre sous forme de dictionnaire. | Très utilisé comme zone d'extension, mais sans schéma commun. |

Le constructeur impose seulement `object_type`, `object_id` et un message lisible non vide. Si `readable_message` est vide, il est remplacé par `rule_code` ou par `calculation_result`.

### `Anomaly`

`Anomaly` représente un problème détecté à partir d'un résultat ou d'une donnée métier. Les champs actuellement disponibles sont les suivants.

| Champ | Rôle actuel | Usage observé |
| --- | --- | --- |
| `id`, `created_at`, `updated_at` | Identité technique héritée de `Entity`. | Utilisé comme identifiant de ligne dans le tableau de contrôle. |
| `object_type` | Type d'objet concerné. | Obligatoire ; affiché et utilisé pour trier les lignes. |
| `object_id` | Identifiant de l'objet concerné. | Obligatoire ; affiché et utilisé pour trier les lignes. |
| `person_id` | Identifiant de la personne concernée. | Restitué dans les lignes et vues de contrôle. |
| `contract_id` | Identifiant du contrat concerné. | Très utilisé pour filtrer les anomalies contrat. |
| `assignment_id` | Identifiant de l'affectation concernée. | Utilisé pour filtrer les anomalies affectation. |
| `calculation_result_id` | Lien vers le résultat qui a produit l'anomalie. | Alimenté par les contrôles, mais non exploité par les services actuels. |
| `level` | Niveau de gravité (`INFO`, `ATTENTION`, `BLOCKING`). | Utilisé pour les compteurs, le tri et l'affichage. |
| `code` | Code métier d'anomalie. | Très utilisé dans les vues et tests. |
| `message` | Message utilisateur court. | Très utilisé dans les lignes de contrôle. |
| `details` | Complément libre. | Utilisé pour quelques anomalies quantitatives ; absent sur plusieurs anomalies simples. |
| `detection_date` | Date de détection. | Alimentée par les contrôles ; pas encore restituée dans les vues actuelles. |
| `resolved` | Indique si l'anomalie est résolue. | Très utilisé pour filtrer les anomalies actives et les compteurs. |
| `resolution_date` | Date de résolution. | Prévu pour le cycle de vie ; non exploité dans les services actuels. |
| `resolved_by_user_id` | Utilisateur ayant résolu. | Prévu pour audit ; non exploité dans les services actuels. |
| `resolution_comment` | Commentaire de résolution. | Prévu pour audit ; non exploité dans les services actuels. |

Le constructeur impose `object_type`, `object_id`, `code` et `message`.

## Champs réellement utilisés

Les champs les plus structurants aujourd'hui sont :

- pour relier le résultat à son périmètre : `object_type`, `object_id`, `person_id`, `contract_id`, `assignment_id` ;
- pour identifier la règle ou le problème : `rule_code`, `code`, `level`, `status` ;
- pour restituer une première explication courte : `readable_message`, `message` ;
- pour les contrôles chiffrés : `actual_value`, `theoretical_value`, `gap`, `retained_base`, `retained_coefficient` ;
- pour les contrôles documentés : `rule_reference_code`, `legal_certainty` ;
- pour le cycle de vie des anomalies : `resolved`.

## Champs rares, peu exploités ou hétérogènes

- `CalculationResult.rule_id` existe mais les contrôles actuels s'appuient surtout sur `rule_code`.
- `CalculationResult.rule_reference_code` et `legal_certainty` sont présents seulement sur certains contrôles raccordés aux références CCNS. Les contrôles plus anciens ou plus génériques n'exposent pas encore cette traçabilité.
- `Anomaly.calculation_result_id` est presque toujours alimenté lorsque l'anomalie vient d'un résultat, mais les services de restitution ne l'utilisent pas encore pour enrichir l'affichage.
- Les champs de résolution (`resolution_date`, `resolved_by_user_id`, `resolution_comment`) préparent un cycle de vie complet, mais seul `resolved` est réellement pris en compte.
- `details` est précieux mais non normalisé : certaines clés sont très explicites (`salary_grid_code`, `salary_grid_line_id`, `completed_years`), d'autres restent dépendantes du contrôle. Cela rend l'explication automatique possible, mais fragile sans convention.
- `gap` est numériquement utile mais doit être interprété avec le contexte : pour les minima et l'ancienneté, un écart négatif signale un manque ; pour le plafond CEE, un écart positif signale un dépassement.

## Doublons et recouvrements

Plusieurs informations existent à deux endroits ou avec deux granularités :

- `object_id` recoupe souvent `contract_id` lorsque `object_type == "contract"` ; ce doublon est utile pour les filtres mais doit être assumé dans l'explication.
- `Anomaly.code` et `CalculationResult.rule_code` décrivent deux niveaux différents : la règle contrôlée et le problème détecté. Il ne faut pas les fusionner, mais le futur moteur devra les présenter ensemble.
- `readable_message` et `Anomaly.message` sont deux messages courts. Le premier explique le résultat du contrôle ; le second explique le problème détecté. Ils peuvent sembler redondants lorsque le résultat est non conforme.
- Certaines valeurs chiffrées sont à la fois dans les champs typés et dans `details` : par exemple salaire réel, minimum théorique ou écart peuvent être présents dans une anomalie et dans le résultat relié.
- La référence réglementaire existe déjà au niveau des règles (`CalculationRule`, `RuleReference`, `RuleVersion`) et au niveau de certains résultats (`rule_reference_code`, `legal_certainty`). Ce recouvrement est souhaitable pour figer la trace du résultat, mais il manque un mécanisme standard d'hydratation de l'explication depuis la référence.

## Informations perdues ou insuffisamment explicites

Les résultats actuels permettent de comprendre le constat, mais pas toujours le raisonnement complet. Les principales pertes d'information sont :

- la source exacte de chaque donnée utilisée : valeur saisie, valeur issue d'une grille, valeur calculée, valeur par défaut ou valeur déduite ;
- les unités (`€ mensuel`, `€ annuel`, `heures`, `jours`, `pourcentage`) hors conventions implicites ;
- la période contrôlée et la période de validité de la règle, lorsque seule une date de calcul est disponible ;
- l'identifiant de version de règle retenue, même lorsque des `RuleVersion` existent par ailleurs ;
- le libellé complet de la règle et de la référence réglementaire, lorsque seul un code est copié dans le résultat ;
- les alternatives non retenues : autres lignes de grille candidates, autres barèmes, raisons de non-applicabilité ;
- la formule textuelle complète du calcul ;
- la recommandation opérationnelle contextualisée, par exemple corriger une classification, renseigner une grille ou vérifier un salaire ;
- le niveau de confiance interprétable par un utilisateur métier, distinct du `legal_certainty` technique.

## Points de branchement possibles

Sans changer les calculs, un futur moteur d'explication pourra se brancher à quatre endroits simples.

1. **Après production du couple `(CalculationResult, Anomaly | None)`**  
   Chaque fonction de contrôle retourne déjà un résultat et éventuellement une anomalie. C'est le point le moins intrusif pour construire une explication en lecture seule.

2. **Dans les services de contrôle applicatifs**  
   `ContractControlService`, `AssignmentControlService` et `ControlDashboardService` agrègent déjà résultats et anomalies pour les vues. Ils pourront recevoir des objets d'explication prêts à afficher, sans porter la logique métier.

3. **Dans les dépôts de résultats et anomalies**  
   Les dépôts savent filtrer par contrat, affectation et résolution. Un service d'explication pourra récupérer le résultat relié via `Anomaly.calculation_result_id` puis enrichir l'anomalie.

4. **Dans la couche règles/références**  
   Les entités `CalculationRule`, `RuleVersion` et `RuleReference` contiennent déjà le label, la référence, la période, le statut documentaire, la certitude et le mode de calcul. Le moteur d'explication devra les consulter, mais ne devra pas recalculer la règle.

## Demain : architecture proposée

Cette PR ne crée pas encore de nouveaux objets. L'architecture cible peut rester simple et additive.

### Objet d'explication cible

Un futur objet, par exemple `ControlExplanation`, pourrait être construit en lecture seule à partir de `CalculationResult`, `Anomaly`, `CalculationRule`, `RuleVersion`, `RuleReference` et des données d'entrée déjà disponibles. Il pourrait exposer :

- `summary` : résumé utilisateur en une phrase ;
- `detailed_explanation` : déroulé détaillé du contrôle ;
- `regulatory_reference` : titre, source, URL, période et niveau de certitude ;
- `confidence_level` : niveau de confiance lisible, dérivé de la certitude juridique, du statut de référence et de la complétude des données ;
- `used_data` : liste structurée des données utilisées, avec valeur, unité, origine et date ;
- `formula` : formule ou logique de comparaison en texte ;
- `recommendation` : action suggérée si l'état n'est pas conforme ou si les données sont incomplètes ;
- `limitations` : limites connues, hypothèses, données manquantes ou contrôle non applicable.

### Service de construction

Un service applicatif léger, par exemple `ControlExplanationService`, pourrait :

1. recevoir un `CalculationResult` et éventuellement son `Anomaly` ;
2. récupérer la règle par `rule_code` ou `rule_id` ;
3. récupérer la version applicable à `calculation_date` lorsque la règle a des versions ;
4. récupérer la référence réglementaire via `rule_reference_code` ou via la version ;
5. interpréter les champs quantitatifs selon un petit catalogue de règles d'affichage ;
6. produire une explication sans modifier le résultat ni l'anomalie.

### Catalogue d'adaptateurs par contrôle

Pour éviter une refonte, le moteur peut commencer par un catalogue d'adaptateurs optionnels :

- adaptateur générique pour tout résultat : affiche message, statut, code, dates et détails ;
- adaptateur minimum de grille : explique classification, grille, ligne, minimum, salaire réel et écart ;
- adaptateur ancienneté : explique groupe, date de départ, années complètes, taux, base SMC et montant attendu ;
- adaptateur plafond CEE : explique période glissante, nombre de jours, seuil et dépassement ;
- adaptateur données manquantes : explique la donnée absente et l'action recommandée.

Un contrôle sans adaptateur spécifique resterait explicable par l'adaptateur générique.

### Recommandations de données minimales à stabiliser plus tard

Sans changer les calculs, une future PR pourra normaliser progressivement :

- `details["inputs"]` : données d'entrée utilisées ;
- `details["formula"]` : formule textuelle ou code de formule ;
- `details["unit"]` ou unités par valeur ;
- `details["source"]` : origine des données ;
- `details["rule_version"]` : version retenue si disponible ;
- `details["non_applicability_reason"]` : raison structurée lorsqu'un contrôle ne s'applique pas.

Ces conventions doivent rester additives et compatibles avec les détails existants.

## Audit des contrôles à expliquer en priorité

### Priorité haute

1. **Minimum conventionnel depuis la grille (`MINIMUM_FROM_GRID`)**  
   Impact métier fort : salaire, classification, grille historique, ligne applicable, proratisation et écart. C'est le meilleur candidat pour une explication détaillée car les données chiffrées et la référence réglementaire sont déjà bien présentes.

2. **Montant de prime d'ancienneté (`CCNS_SENIORITY_AMOUNT`)**  
   Impact métier fort : date de référence, ancienneté complète, groupe, base SMC groupe 3, taux plafonné et montant théorique. Le contrôle contient déjà le taux et les années complètes dans `details`, mais il manque une formule textuelle et l'unité.

3. **Données bloquantes de contrat (`CONTRAT_SANS_CLASSIFICATION`, `CONTRAT_SANS_GRILLE`, `REGLE_INTROUVABLE`)**  
   Ces anomalies empêchent ou fragilisent d'autres contrôles. Une explication doit indiquer la donnée manquante, l'effet sur les calculs et l'action attendue.

4. **Plafond CEE 80 jours (`CEE_MAX_80J`)**  
   Impact de conformité fort et gravité bloquante en cas de dépassement. L'explication doit clarifier la période glissante, le seuil et le nombre de jours retenu.

### Priorité moyenne

1. **Applicabilité de l'ancienneté (`SENIORITY_APPLICABILITY`)**  
   Utile pour comprendre pourquoi une prime est applicable ou non selon le groupe. Les données sont présentes mais l'enjeu est moindre que le montant final.

2. **Barème apprentissage (`APPRENTICESHIP_SCALE`)**  
   Utile lorsque l'âge ou l'année d'exécution ne correspond à aucun barème. L'explication devra distinguer donnée invalide, barème absent et cas couvert.

3. **Majoration temps partiel court (`SHORT_PART_TIME_MAJO`)**  
   Le contrôle est simple mais très lisible à expliquer : seuil d'heures, palier et coefficient.

4. **Rémunération de base absente (`REMUNERATION_BASE_ABSENTE`)**  
   Ce cas mérite une recommandation claire, même si l'explication métier est moins complexe.

### Priorité faible

1. **Contrôles de présence simples (`CONTRACT_HAS_CLASSIFICATION`, `CONTRACT_HAS_SALARY_GRID`) lorsqu'ils sont conformes**  
   Le message actuel suffit généralement.

2. **Résultats informatifs sans anomalie et sans enjeu chiffré**  
   Ils pourront passer par l'adaptateur générique.

3. **Champs de résolution des anomalies**  
   Ils seront importants pour un historique utilisateur, mais ne sont pas prioritaires pour expliquer le calcul initial.

## Risques à éviter

- Ne pas déplacer la logique métier dans le moteur d'explication.
- Ne pas recalculer les salaires ou les seuils pour produire un texte.
- Ne pas supposer qu'un `gap` négatif ou positif a toujours le même sens sans connaître le contrôle.
- Ne pas rendre obligatoire un schéma `details` rétroactivement ; les conventions doivent être progressives.
- Ne pas confondre certitude juridique, statut documentaire et confiance utilisateur.

## Conclusion

Les objets actuels contiennent déjà une base solide : périmètre, code de règle, statut, valeurs chiffrées, écart, message et parfois référence réglementaire. Le principal manque n'est pas le résultat, mais la traçabilité explicite du raisonnement : origine des données, unités, formule, version de règle et recommandation. Le futur moteur d'explication peut donc être ajouté comme une couche de lecture, branchée après les contrôles existants, sans modifier les règles métier ni les calculs.
