# Niveau de confiance juridique des contrôles CCNS

## Objectif

Le moteur CCNS ne produit pas seulement un état `conforme` ou `non conforme` : il doit aussi signaler la solidité juridique du contrôle qui a conduit au résultat. Deux contrôles peuvent être techniquement fiables tout en reposant sur des bases juridiques différentes : texte impératif clair, interprétation majoritaire, usage de branche, accord local ou règle interne.

Cette notion n'entraîne aucun changement de calcul. Elle enrichit les métadonnées exposées par les règles et par les résultats afin de préparer une restitution future du type :

```text
⚠ Analyse recommandée

Cette règle dépend du contexte d'application.
```

## Niveaux retenus

Les niveaux sont portés par `LegalCertainty` dans le domaine moteur.

| Niveau | Signification | Usage attendu |
| --- | --- | --- |
| `CERTAINE` | Le texte officiel est clair et le contrôle est objectif. | Exemple : rémunération inférieure au minimum conventionnel applicable. |
| `MAJORITAIRE` | Un texte existe et son interprétation est largement admise, avec peu de divergences identifiées. | Exemple : prime d'ancienneté standard modélisée par le moteur actuel. |
| `DISCUTEE` | Plusieurs interprétations existent ou la jurisprudence et les pratiques peuvent varier. | À utiliser lorsque le moteur détecte un risque mais ne doit pas présenter l'analyse comme certaine. |
| `CONTEXTUELLE` | Le résultat dépend fortement de l'organisation, de l'activité, d'accords applicables ou du contexte de travail. | Préparer un affichage invitant à l'analyse humaine. |
| `INTERNE` | Règle propre à Teamworks ou à l'association, non directement imposée par un texte réglementaire. | Contrôles de gestion, qualité de donnée ou politique interne. |

## Différence avec la traçabilité réglementaire

La traçabilité réglementaire répond à la question : **quelle source justifie la règle ?** Elle identifie une référence, une URL, une date d'effet, un article ou une version documentaire.

La confiance juridique répond à une autre question : **avec quel niveau de certitude peut-on qualifier le résultat produit par cette règle ?** Une règle peut disposer d'une source documentée tout en restant contextuelle ou discutée si son application dépend d'accords particuliers, d'une jurisprudence variable ou d'éléments non connus par le moteur.

## Différence avec la veille réglementaire

La veille réglementaire répond à la question : **la source ou la règle a-t-elle évolué ?** Elle sert à détecter qu'un texte, une valeur ou une interprétation doit être revu.

La confiance juridique décrit l'état d'analyse à un instant donné. Elle peut évoluer à la suite de la veille, mais elle n'est pas une date de validité ni un statut de version. Par exemple, une règle `MAJORITAIRE` peut devenir `CERTAINE` après clarification par un avenant, ou `DISCUTEE` après une décision de justice divergente.

## Évolution d'un niveau

Le niveau d'une règle doit pouvoir évoluer sans modifier le calcul lorsque seule l'appréciation juridique change :

1. identifier l'événement déclencheur : nouveau texte, jurisprudence, avis de branche, retour d'audit ou accord local ;
2. documenter la source dans `RuleReference` ou dans une version de règle ;
3. modifier le niveau `LegalCertainty` associé ;
4. conserver dans le commentaire ou la documentation la raison du changement ;
5. ajouter ou adapter les tests uniquement pour vérifier l'exposition de la métadonnée, sans changer les montants calculés.

## Intégration actuelle

Le modèle permet désormais :

- à une `RuleReference` de porter un niveau de confiance juridique ;
- à une `CalculationRule` de surcharger ce niveau si nécessaire ;
- à un `CalculationResult` d'exposer le niveau utilisé par un contrôle.

Deux règles existantes sont raccordées :

- minimum conventionnel depuis grille : `CERTAINE`, car la comparaison à un minimum conventionnel applicable est un contrôle objectif ;
- prime d'ancienneté standard groupes 1 à 6 : `MAJORITAIRE`, car le moteur reprend une interprétation standard documentée, tout en laissant la place à une revue juridique future selon les cas particuliers.

## Limites connues

Cette évolution ne remplace pas une analyse juridique humaine. Elle ne masque pas les anomalies et ne baisse pas leur gravité. Elle prépare seulement l'interface et les exports à distinguer les contrôles objectivement établis des contrôles nécessitant davantage de contexte.
