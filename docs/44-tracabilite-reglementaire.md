# Traçabilité réglementaire des règles CCNS

## Objectif

Le moteur CCNS sait contrôler des situations contractuelles. La traçabilité réglementaire ajoute une couche d'explication : chaque règle métier importante pourra être reliée progressivement à sa source officielle, à sa période de validité et à sa version documentaire.

Cette évolution ne modifie ni les calculs, ni les montants, ni les règles applicables. Elle enrichit les résultats afin de pouvoir répondre à la question : « Cette règle provient de quelle source ? ».

## Modèle introduit

Le modèle `RuleReference` décrit une référence réglementaire indépendante de wxPython et des écrans. Il contient notamment :

- un code stable ;
- un titre lisible ;
- la source officielle ;
- l'URL officielle ;
- l'organisme ou les organismes associés ;
- la référence juridique ;
- une date d'effet et une date de fin optionnelle ;
- une version ;
- un commentaire ;
- un statut ;
- un niveau de confiance ;
- un mode de calcul explicatif.

Les règles métier peuvent pointer vers une `RuleReference`, et les résultats de contrôle peuvent exposer un `rule_reference_code`. Les règles non encore documentées continuent donc de fonctionner sans référence.

## Articulation avec la veille réglementaire

La veille réglementaire détecte les avenants, textes consolidés ou modifications de grille. La traçabilité réglementaire sert de point de raccordement entre cette veille et le moteur :

1. la veille identifie une source officielle nouvelle ou modifiée ;
2. une nouvelle `RuleReference` est créée avec son code, sa version et sa date d'effet ;
3. la règle métier existante reste inchangée tant que le calcul n'est pas validé ;
4. lorsque la mise à jour métier est prête, la règle pointe vers la nouvelle référence ;
5. l'ancienne référence reçoit une date de fin ou un statut `SUPERSEDED` si elle est remplacée.

Cette séparation évite qu'une détection réglementaire entraîne automatiquement une modification de calcul non validée.

## Évolution d'une règle

Une règle peut évoluer selon deux axes distincts :

- **documentation seule** : amélioration du lien officiel, précision de l'article, changement du niveau de confiance ;
- **évolution métier** : nouvelle date d'effet, nouveau barème, nouvelle formule ou nouvelle population concernée.

Dans le premier cas, seule la référence réglementaire change. Dans le second cas, une nouvelle version de la référence est créée, puis le calcul est adapté dans une PR dédiée avec tests métier.

## Remplacement progressif d'une version

Lorsqu'une nouvelle version remplace une ancienne :

1. conserver l'ancienne référence pour expliquer les contrôles historiques ;
2. renseigner sa date de fin lorsqu'elle est connue ;
3. créer une nouvelle référence avec une date d'effet explicite ;
4. raccorder les règles applicables à partir de cette date ;
5. ajouter les tests nécessaires pour vérifier que l'ancien et le nouveau périmètre restent distinguables.

Cette logique permettra de comparer deux versions d'une même règle et de produire des rapports d'audit datés.

## Premiers raccordements

La première intégration raccorde uniquement quelques règles simples :

- la prime d'ancienneté standard des groupes 1 à 6 ;
- les minima mensuels conventionnels des groupes 1 à 6.

Les autres règles restent opérationnelles sans référence réglementaire. Leur raccordement devra se faire progressivement, au rythme des revues documentaires et juridiques.

## Vision long terme

Cette architecture prépare :

- l'affichage de la source officielle dans l'interface ;
- la justification d'un contrôle auprès d'un salarié ;
- la production d'un rapport d'audit ;
- la préparation d'une mise à jour lorsqu'un avenant est détecté ;
- la comparaison entre deux versions d'une même règle.
