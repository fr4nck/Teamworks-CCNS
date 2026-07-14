# Guide opérationnel des agents Teamworks-CCNS

Ce fichier est la porte d'entrée pour toute intervention dans le dépôt. Il résume les règles à appliquer et renvoie vers les documents de référence lorsque le détail est nécessaire.

## Priorités générales

Respecter l'ordre suivant lors des arbitrages :

1. exactitude métier ;
2. stabilité ;
3. lisibilité ;
4. simplicité ;
5. compatibilité ;
6. performances ;
7. micro-optimisations.

Ne jamais améliorer un point technique au prix d'une règle CCNS fausse, d'une régression fonctionnelle ou d'un comportement moins compréhensible.

## Performances

- Mesurer avant d'optimiser.
- Éviter les requêtes répétées, les schémas N+1, les `SELECT *` inutiles et les traitements redondants.
- Ne pas bloquer inutilement le fil graphique wxPython ; différer ou découper les traitements longs lorsque c'est possible.
- Privilégier les améliorations locales, mesurables, réversibles et documentées.
- Conserver le diagnostic de performance désactivé par défaut.
- Appliquer les règles détaillées de `docs/34-performance.md` et consulter `docs/AUDIT_PERFORMANCES.md` avant toute optimisation intrusive.

## Compatibilité

Les évolutions doivent tenir compte des environnements réellement visés :

- Windows 11 ;
- versions récentes de Windows Server ;
- distributions Linux maintenues ;
- versions récentes de macOS ;
- architectures Intel et Apple Silicon lorsque les dépendances le permettent ;
- versions récentes et supportées de Python.

Avant de valider une modification, vérifier la matrice `docs/MATRICE_COMPATIBILITE.md`, notamment pour les dépendances binaires, les chemins, l'encodage, les fins de ligne, les accès réseau et les usages en bureau distant.

## Dépendances et API

Avant d'ajouter ou de mettre à jour une dépendance :

- vérifier son activité et son historique de maintenance ;
- vérifier sa licence ;
- vérifier sa compatibilité Windows, Linux et macOS ;
- vérifier sa compatibilité avec les versions récentes de Python ;
- identifier les API obsolètes ou dépréciées ;
- éviter les dépendances lourdes lorsqu'une solution standard ou déjà présente suffit.

Les règles détaillées sont dans `docs/35-perennite-technique.md`. Les dépendances actuelles doivent être relues avec la matrice de compatibilité avant tout changement de version.

## Refontes structurelles

Une refonte n'est pas interdite, mais elle doit reposer sur :

- des mesures reproductibles ;
- un goulot d'étranglement clairement identifié ;
- une comparaison avec les correctifs locaux ;
- une estimation du gain ;
- une couverture suffisante des règles métier ;
- un plan de migration progressif ;
- une stratégie de retour arrière.

Privilégier une migration par couches ou modules plutôt qu'une réécriture globale immédiate. Utiliser `docs/35-perennite-technique.md`, `docs/33-modernisation-optimisation-sobriete-teamworks-ccns.md` et `docs/FEUILLE_ROUTE_MAINTENANCE.md` pour décider entre correction locale, mutualisation progressive et modernisation structurelle.

## Vérifications minimales

Pour une modification de code, documenter dans la PR :

- les tests ou commandes exécutés ;
- les mesures avant/après lorsqu'une performance est concernée ;
- les environnements ou versions réellement vérifiés ;
- les limites connues et les risques de régression.

Si l'application graphique est modifiée de manière perceptible, prévoir une vérification manuelle wxPython adaptée à l'écran concerné.

## Git et Pull Requests

- Travailler sur une branche dédiée.
- Produire des commits thématiques en français.
- Rédiger les PR en français.
- Décrire le problème, la solution, les tests, les mesures, les limites et les risques.
- Ne jamais fusionner automatiquement.
