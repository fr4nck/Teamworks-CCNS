# Feuille de route centrale Teamworks-CCNS

## Statut du document

Ce document est la **référence centrale du projet** pour :

- l’ordre des travaux ;
- le registre des lots `TW-*` ;
- leur état ;
- les liens vers les PR correspondantes ;
- les critères de sortie ;
- l’estimation consolidée de progression.

Les documents spécialisés restent valables, mais ne doivent plus porter une roadmap concurrente. Ils détaillent un domaine et renvoient ici pour la planification.

**Dernière consolidation : 29 juillet 2026**  
**Progression globale estimée : 69 %**  
**Migration Python 3 / wxPython Phoenix estimée : 88 %**

> Les pourcentages sont des indicateurs de pilotage, pas une mesure automatique. Ils doivent être révisés après chaque lot significatif et justifiés par des éléments intégrés et testés.

---

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
| Architecture et évolution long terme | `docs/ARCHITECTURE_EVOLUTION.md` |
| Plan d'intégration historique à court terme | `docs/31-plan-integration-court-terme.md` |
| Cartographie fonctionnelle et technique | `docs/30-cartographie-teamworks-ccns.md` |

---

## Règles du registre TW

Chaque intervention planifiée reçoit un identifiant stable `TW-<numéro>`.

États autorisés :

- `À cadrer` ;
- `Prêt` ;
- `En cours` ;
- `Bloqué` ;
- `À valider` ;
- `Terminé` ;
- `Abandonné`.

Un lot n'est `Terminé` que si :

1. le code ou la documentation est intégré au dépôt cible ;
2. la CI utile est verte ;
3. le test ciblé ou la vérification reproductible existe ;
4. les workflows temporaires ont été retirés ou explicitement conservés ;
5. cette feuille de route est mise à jour.

Les numéros déjà utilisés dans les branches, commits, issues ou PR ne doivent jamais être réattribués.

---

## Registre actif — migration Python 3 / wxPython Phoenix

| TW | Objet | État | Référence | Critère de sortie |
| --- | --- | --- | --- | --- |
| TW-100 | Remplacer les fallbacks Classic de `getShadow()` par `wx.Image(...)` | Terminé | PR #171 | code Phoenix direct et test ciblé intégrés |
| TW-101 | Remplacer le fallback `SetAlphaData()` de `ThumbnailCtrl` par `wx.Image.SetAlpha()` | En cours | PR #172 | correctif appliqué, test ciblé vert, workflow temporaire retiré |
| TW-102 | Recenser et remplacer les usages résiduels de `wx.BitmapFromImage` | À cadrer | — | inventaire exact, remplacement testé, aucune régression visuelle connue |
| TW-103 | Recenser et remplacer les usages résiduels de `wx.ImageFromBitmap` | À cadrer | — | inventaire exact et API Phoenix directe |
| TW-104 | Recenser et remplacer les usages résiduels de `wx.EmptyBitmap` | À cadrer | — | API Phoenix directe et compilation verte |
| TW-105 | Recenser et remplacer les usages résiduels de `wx.EmptyImage` | À cadrer | — | API Phoenix directe et compilation verte |
| TW-106 | Auditer les autres API wxPython Classic obsolètes | À cadrer | — | rapport d'inventaire priorisé et lots dédiés créés |
| TW-107 | Éliminer les derniers branchements `six.PY2` / `six.PY3` | À cadrer | — | aucune branche de compatibilité Python 2 utile restante |
| TW-108 | Réduire puis supprimer `six` lorsqu'il n'est plus nécessaire | À cadrer | — | usages inventoriés, substitutions testées, dépendance retirée si possible |
| TW-109 | Audit Phoenix final du dépôt | À cadrer | — | audit reproductible sans incompatibilité bloquante connue |
| TW-110 | Stabiliser les widgets critiques après migration | À cadrer | — | tests ciblés et parcours manuels documentés |
| TW-111 | Stabiliser la CI de migration | À cadrer | — | workflows pérennes, temporaires supprimés, checks fiables |
| TW-112 | Renforcer la couverture des chemins critiques | À cadrer | — | seuil défini sur les modules ciblés, pas de pourcentage global arbitraire |
| TW-113 | Geler la migration Python 3 / Phoenix | À cadrer | — | matrice de compatibilité et documentation mises à jour |

Les lots TW-102 à TW-113 sont des **lots prévisionnels**. Leur périmètre doit être confirmé par recherche dans le dépôt avant création d'une branche ou d'une PR. Ils ne constituent pas la preuve qu'un usage obsolète existe encore.

---

## Axes fonctionnels et techniques

| Domaine | Progression indicative | Prochain résultat attendu |
| --- | ---: | --- |
| Migration Python 3 / Phoenix | 88 % | terminer TW-101 puis produire l'inventaire réel des API Classic restantes |
| Couverture de tests automatiques | 62 % | protéger les chemins migrés et les API publiques critiques |
| Audit de compatibilité | 83 % | transformer les constats restants en lots TW vérifiables |
| Couche SQLite / encodages | 90 % | empêcher toute régression sur chemins bytes et encodages |
| Widgets wxPython | 80 % | stabiliser les composants réellement utilisés |
| Contrôles CCNS | 75 % | renforcer les cas métier spécifiques et leur traçabilité documentaire |
| Calculs de paie | 70 % | consolider les règles et exports sans prétendre remplacer un logiciel de paie |
| Exports | 72 % | fiabiliser les formats paie/comptabilité et les contrôles avant export |
| Imports | 58 % | consolider les correspondances et rejets explicites |
| Gestion du personnel | 72 % | terminer les raccords avec les écrans Teamworks existants |
| Refonte UI | 30 % | définir le lot après stabilisation technique |
| Thème sombre | 0 % | cadrer après gel Phoenix et audit des widgets |
| Performances | 20 % | mesurer avant/après sur des parcours représentatifs |
| Documentation développeur | 55 % | maintenir cette roadmap et réduire les documents contradictoires |
| Packaging Windows | 45 % | fixer la version Python cible et produire un paquet reproductible |
| Installation simplifiée | 35 % | procédure testée sur poste vierge |
| Qualité / CI | 78 % | supprimer les workflows d'application temporaires et conserver les gardes pérennes |

---

## Priorités consolidées

### Phase 1 — Fin de migration et stabilisation

1. terminer TW-101 ;
2. inventorier réellement les API Classic restantes ;
3. créer uniquement les lots confirmés par cet inventaire ;
4. retirer les workflows temporaires ;
5. maintenir une CI verte et reproductible.

### Phase 2 — Consolidation métier CCNS

1. stabiliser les raccords aux écrans Teamworks existants ;
2. consolider l'audit par individu et par contrat ;
3. renforcer les règles CCNS, alternance, CEE, mineurs et temps de travail ;
4. fiabiliser imports et exports ;
5. documenter chaque règle avec sa source et sa date d'effet.

### Phase 3 — Produit utilisable et diffusable

1. modernisation mesurée de l'interface ;
2. thème sombre ;
3. packaging Windows reproductible ;
4. installation simplifiée ;
5. documentation utilisateur et procédure de migration des bases.

---

## Priorités de maintenance

| Priorité | Zone | Pourquoi | Première action exploitable | Critère de sortie |
| --- | --- | --- | --- | --- |
| 1 | Mesures reproductibles | Sans mesure, les optimisations risquent d'être anecdotiques | collecter les catégories existantes `connexion`, `sql`, `sql_fetch`, `transformation_python`, `widget`, `total_action` sur une base représentative | tableau avant/après joint à la PR |
| 2 | Référentiels et lectures répétées | Les relectures complètes peuvent pénaliser fiches et listes | cartographier les `SELECT *`, `fetchall()` et lectures sans filtre dans les écrans les plus utilisés | liste des requêtes priorisées par fréquence et volume |
| 3 | Service partagé CCNS | Plusieurs écrans consomment les mêmes données CCNS | définir une interface minimale de lecture contrats/classifications/grilles sans modifier les règles métier | un écran migré avec résultats identiques |
| 4 | Interface wxPython | Le rendu peut bloquer l'utilisateur, surtout à distance | mesurer remplissage, `Refresh()`, `Layout()`, `Fit()` et reconstructions complètes | réduction mesurée du temps de rendu ou justification d'abandon |
| 5 | Compatibilité dépendances | Les bibliothèques natives conditionnent Python moderne et macOS ARM | auditer `requirements.txt` avec la matrice, sans mise à jour massive | écarts documentés et lots de mise à jour séparés |
| 6 | Packaging | Le packaging reflète encore une cible Windows/Python historique | isoler les hypothèses Python 3.7 / win32 dans `setup.py` | décision documentée : conserver, moderniser ou remplacer par lot dédié |

---

## Correctif local ou modernisation structurelle ?

| Situation observée | Décision recommandée |
| --- | --- |
| Un écran exécute deux fois la même requête ou le même calcul | correctif local mesuré et réversible |
| Plusieurs écrans dupliquent la même lecture CCNS | mutualisation progressive dans un service partagé |
| Une dépendance est seulement bruyante mais encore maintenue | correction locale des API dépréciées |
| Une dépendance bloque une plateforme cible ou une version Python supportée | dossier de migration avec alternatives et retour arrière |
| Une connexion globale semble plus rapide sur un poste | ne pas généraliser sans mesure réseau, concurrence et perte de connexion |
| Les correctifs locaux deviennent nombreux, risqués et incohérents | dossier de refonte selon `docs/35-perennite-technique.md` |

---

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

---

## Critères d'acceptation d'une intervention

Une intervention est exploitable si elle fournit :

- une règle ou un comportement clairement relié à un document de référence ;
- des tests ou vérifications reproductibles ;
- des mesures lorsqu'elle annonce un gain de performance ;
- une analyse de compatibilité lorsque dépendances, Python, OS, réseau ou packaging sont concernés ;
- une limite connue et une stratégie de retour arrière pour les changements risqués ;
- la mise à jour du registre TW et de la progression lorsqu'elle modifie le périmètre du projet.
