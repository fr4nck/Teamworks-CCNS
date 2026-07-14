# Feuille de route de maintenance Teamworks-CCNS

## Objectif

Cette feuille de route relie les audits existants, les règles de performance, la pérennité technique et la matrice de compatibilité. Elle sert à choisir les prochains travaux sans dupliquer les documents spécialisés.

## Documents de référence

| Besoin | Document à consulter |
| --- | --- |
| Règles opérationnelles pour agents | `AGENTS.md` |
| Règles de performance | `docs/34-performance.md` |
| Audit et mesures de performance | `docs/AUDIT_PERFORMANCES.md` |
| Plan détaillé d'optimisation | `docs/PLAN_OPTIMISATION_PERFORMANCES.md` |
| Optimisation déjà réalisée sur l'accueil | `docs/optimisation_accueil_ccns.md` |
| Pérennité, dépendances, API et refontes | `docs/35-perennite-technique.md` |
| Modernisation et service de lecture CCNS | `docs/33-modernisation-optimisation-sobriete-teamworks-ccns.md` |
| Compatibilité réelle | `docs/MATRICE_COMPATIBILITE.md` |

## Constats consolidés

- Les règles de performance, de compatibilité et de refonte existent déjà, mais elles étaient dispersées entre plusieurs documents.
- L'accueil CCNS a déjà été optimisé : ne pas recréer ce travail, mais utiliser ses mesures et son cache court comme exemple de changement local et réversible.
- L'audit de performances identifie des zones prioritaires : accès base, listes volumineuses, référentiels, planning, rendu wxPython et stratégies de connexion.
- La modernisation doit rester progressive : brancher, tester, mesurer, puis mutualiser ou refondre seulement si les faits le justifient.

## Priorités de maintenance

| Priorité | Zone | Pourquoi | Première action exploitable | Critère de sortie |
| --- | --- | --- | --- | --- |
| 1 | Mesures reproductibles | Sans mesure, les optimisations risquent d'être anecdotiques | collecter les catégories existantes `connexion`, `sql`, `sql_fetch`, `transformation_python`, `widget`, `total_action` sur une base représentative | tableau avant/après joint à la PR |
| 2 | Référentiels et lectures répétées | Les relectures complètes peuvent pénaliser fiches et listes | cartographier les `SELECT *`, `fetchall()` et lectures sans filtre dans les écrans les plus utilisés | liste des requêtes priorisées par fréquence et volume |
| 3 | Service partagé CCNS | Plusieurs écrans consomment les mêmes données CCNS | définir une interface minimale de lecture contrats/classifications/grilles sans modifier les règles métier | un écran migré avec résultats identiques |
| 4 | Interface wxPython | Le rendu peut bloquer l'utilisateur, surtout à distance | mesurer remplissage, `Refresh()`, `Layout()`, `Fit()` et reconstructions complètes | réduction mesurée du temps de rendu ou justification d'abandon |
| 5 | Compatibilité dépendances | Les bibliothèques natives conditionnent Python moderne et macOS ARM | auditer `requirements.txt` avec la matrice, sans mise à jour massive | écarts documentés et lots de mise à jour séparés |
| 6 | Packaging | Le packaging reflète encore une cible Windows/Python historique | isoler les hypothèses Python 3.7 / win32 dans `setup.py` | décision documentée : conserver, moderniser ou remplacer par lot dédié |

## Correctif local ou modernisation structurelle ?

| Situation observée | Décision recommandée |
| --- | --- |
| Un écran exécute deux fois la même requête ou le même calcul | correctif local mesuré et réversible |
| Plusieurs écrans dupliquent la même lecture CCNS | mutualisation progressive dans un service partagé |
| Une dépendance est seulement bruyante mais encore maintenue | correction locale des API dépréciées |
| Une dépendance bloque une plateforme cible ou une version Python supportée | dossier de migration avec alternatives et retour arrière |
| Une connexion globale semble plus rapide sur un poste | ne pas généraliser sans mesure réseau, concurrence et perte de connexion |
| Les correctifs locaux deviennent nombreux, risqués et incohérents | dossier de refonte selon `docs/35-perennite-technique.md` |

## Vérification des usages réels

Toute PR de maintenance doit préciser si elle touche :

- l'accueil ;
- l'audit CCNS ;
- les dossiers incomplets ;
- la fiche individuelle ;
- les écrans contrats ;
- les listes volumineuses ;
- le planning ou les calendriers ;
- l'installation, les dépendances ou le packaging.

Pour chaque zone touchée, vérifier au minimum que les résultats métier restent identiques, que le rendu utilisateur reste cohérent et que le changement respecte la matrice de compatibilité.

## Jalons proposés

1. **Cadre de maintenance** : AGENTS, matrice et feuille de route alignés.
2. **Mesures terrain** : collecte sur base représentative locale, réseau et bureau distant si disponible.
3. **Réduction des lectures évidentes** : référentiels, `SELECT *`, requêtes répétées et volumes non bornés.
4. **Service partagé CCNS minimal** : mutualisation d'abord sur un chemin consommateur, puis extension aux autres écrans.
5. **Compatibilité Python et dépendances** : corrections locales d'API dépréciées, puis lots de mise à jour testés.
6. **Décisions structurelles** : seulement après mesures, couverture métier et plan de migration.

## Critères d'acceptation d'une intervention

Une intervention est exploitable si elle fournit :

- une règle ou un comportement clairement relié à un document de référence ;
- des tests ou vérifications reproductibles ;
- des mesures lorsqu'elle annonce un gain de performance ;
- une analyse de compatibilité lorsque dépendances, Python, OS, réseau ou packaging sont concernés ;
- une limite connue et une stratégie de retour arrière pour les changements risqués.
