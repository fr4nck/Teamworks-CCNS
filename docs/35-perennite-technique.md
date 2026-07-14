# Pérennité technique

Teamworks-CCNS est un projet de long terme. Les évolutions doivent donc privilégier des choix techniques stables, maintenables et compatibles avec plusieurs générations d'environnements.

Ce document complète les règles de performance et de modernisation continue. Il ne demande pas de refonte générale : il fixe un cadre de décision pour les changements futurs.

---

## Principes généraux

Avant d'utiliser une API, une bibliothèque ou une fonctionnalité récente, vérifier qu'elle :

- n'est pas annoncée comme dépréciée, obsolète ou uniquement maintenue en mode « legacy » ;
- est compatible avec Windows 11, les versions récentes de Windows Server, les distributions Linux supportées et les versions récentes de macOS, Intel comme Apple Silicon ;
- reste compatible avec les versions récentes et prévisibles de Python ;
- dispose d'une documentation stable et d'un chemin de maintenance clair.

Privilégier les API publiques, documentées et largement utilisées. Éviter les dépendances à des comportements internes, expérimentaux ou propres à un seul système d'exploitation.

---

## Compatibilité multiplateforme

Le projet doit rester compatible avec :

- Windows 11 ;
- les versions récentes de Windows Server ;
- les distributions Linux actuellement supportées ;
- les versions récentes de macOS, sur processeurs Intel et Apple Silicon.

Le code ne doit pas dépendre d'un comportement spécifique à un seul système d'exploitation lorsqu'une solution portable existe.

À éviter :

- chemins construits par concaténation avec un séparateur propre à un OS ;
- commandes shell non disponibles partout sans alternative ;
- hypothèses sur l'encodage, la casse des chemins ou les fins de ligne ;
- dépendances binaires non disponibles sur une plateforme cible.

À privilégier :

- les modules standard multiplateformes de Python ;
- les chemins manipulés avec `pathlib` ou des API équivalentes déjà présentes dans le code ;
- les comportements explicitement testés ou documentés sur les plateformes cibles ;
- les adaptations locales et isolées lorsqu'un cas particulier de plateforme est inévitable.

---

## Compatibilité Python

Les évolutions doivent privilégier les API compatibles avec les versions récentes de Python et éviter les fonctions supprimées ou dépréciées.

Lorsqu'une évolution de Python impose une modification, préférer une solution compatible avec plusieurs versions maintenues plutôt qu'un contournement spécifique à une seule version.

Points d'attention :

- consulter les avertissements de dépréciation avant de généraliser une API ;
- éviter les fonctionnalités expérimentales si elles ne sont pas nécessaires ;
- ne pas introduire de syntaxe qui exclut sans besoin une version encore utile au projet ;
- conserver un code lisible plutôt que d'accumuler des branches de compatibilité complexes.

---

## Dépendances

Le nombre de dépendances doit rester limité. Avant d'ajouter une bibliothèque, vérifier :

- son activité et son historique de maintenance ;
- sa compatibilité avec les versions récentes de Python ;
- sa licence ;
- sa disponibilité sur Windows, Linux et macOS ;
- son niveau d'adoption et la clarté de sa documentation.

Privilégier les bibliothèques largement utilisées, maintenues et stables. Une dépendance ne doit être ajoutée que si elle réduit réellement le risque, la complexité ou la charge de maintenance par rapport à une solution interne raisonnable.

Lorsqu'une dépendance devient obsolète, proposer une migration progressive :

1. identifier les usages concernés ;
2. isoler les appels dans une couche simple si nécessaire ;
3. remplacer les usages les plus sûrs en premier ;
4. conserver des tests de non-régression ;
5. retirer l'ancienne dépendance uniquement lorsque les usages ont disparu.

---

## Modernisation continue

Lorsqu'un fichier est modifié, vérifier localement s'il contient aussi :

- des API obsolètes ou annoncées comme dépréciées ;
- des avertissements de dépréciation connus ;
- des incompatibilités probables avec les versions récentes de Python ;
- des hypothèses fragiles vis-à-vis de Windows, Linux ou macOS.

Si une modernisation locale est simple, sûre et sans impact métier, elle peut être intégrée dans la même Pull Request. En revanche, il ne faut pas lancer une refonte générale uniquement pour moderniser des API.

La règle pratique est :

> moderniser ce qui est proche, sûr et utile ; reporter ce qui demande une analyse large.

---

## Critères de décision

Avant de valider un choix technique durable, répondre aux questions suivantes :

- L'API ou la dépendance est-elle stable et non dépréciée ?
- Le choix fonctionne-t-il sur les plateformes cibles ?
- Le choix reste-t-il cohérent avec les versions récentes et prévisibles de Python ?
- Le coût de maintenance est-il inférieur au bénéfice attendu ?
- Existe-t-il une solution plus simple avec la bibliothèque standard ou avec une dépendance déjà présente ?
- Les tests ou vérifications disponibles couvrent-ils le comportement ajouté ?

Si une réponse est incertaine, documenter le doute et choisir l'option la plus stable ou la plus réversible.

---

## Résumé

La pérennité technique de Teamworks-CCNS repose sur des évolutions sobres :

- peu de dépendances ;
- des API stables ;
- une compatibilité multiplateforme explicite ;
- une compatibilité Python maintenue dans la durée ;
- des modernisations locales, progressives et vérifiables.

L'objectif est de faire évoluer le projet sans créer de dette technique évitable ni fragiliser les usages existants.
