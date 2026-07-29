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
**Progression globale estimée : 74 %**  
**Migration Python 3 / wxPython Phoenix estimée : 92 %**

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
| TW-101 | Remplacer le fallback `SetAlphaData()` de `ThumbnailCtrl` par `wx.Image.SetAlpha()` | Terminé | PR #172, merge `1ba77fc0` | correctif appliqué, test ciblé vert, workflow temporaire retiré |
| TW-102 | Vérifier et verrouiller l’absence de `wx.BitmapFromImage` | Terminé | PR #173 | absence confirmée dans le dépôt courant, test permanent vert, CI propre |
| TW-103 | Recenser et remplacer les usages résiduels de `wx.ImageFromBitmap` | Terminé | lots de nettoyage intégrés | inventaire réalisé et API Phoenix directe |
| TW-104 | Recenser et remplacer les usages résiduels de `wx.EmptyBitmap` | Terminé | lots de nettoyage intégrés | API Phoenix directe et compilation verte |
| TW-105 | Recenser et remplacer les usages résiduels de `wx.EmptyImage` | Terminé | lots de nettoyage intégrés | API Phoenix directe et compilation verte |
| TW-106 | Auditer les autres API wxPython Classic obsolètes | Terminé | audit final intégré | rapport d'inventaire traité et gardes CI conservées |
| TW-107 | Éliminer les derniers branchements `six.PY2` / `six.PY3` | Terminé | nettoyage Python 3 intégré | aucune branche de compatibilité Python 2 utile restante |
| TW-108 | Réduire puis supprimer `six` lorsqu'il n'est plus nécessaire | Terminé | nettoyage Python 3 intégré | usages résiduels justifiés ou remplacés |
| TW-109 | Audit Phoenix final du dépôt | Terminé | audits CI actuels | audit reproductible sans incompatibilité bloquante connue |
| TW-110 | Stabiliser les widgets critiques après migration | En cours | lots de stabilisation successifs | tests ciblés et parcours manuels documentés |
| TW-111 | Stabiliser la CI de migration | Terminé | workflows actuels | workflows pérennes, checks fiables et gardes runtime actives |
| TW-112 | Renforcer la couverture des chemins critiques | En cours | suite des tests ciblés | couverture renforcée sur les modules essentiels |
| TW-113 | Geler la migration Python 3 / Phoenix | À valider | — | matrice de compatibilité et documentation mises à jour |
| TW-114 | Produire une version Windows installable intermédiaire | Terminé | packaging Windows intégré | exécutable reproductible, démarrage vérifié et artefact généré |
| TW-115 | Stabiliser les parcours essentiels de la version intermédiaire | Terminé | runtime smoke + contrôles CI | ouverture, ressources essentielles et démarrage vérifiés |
| TW-116 | Introduire un thème sombre pragmatique | Terminé | PR #185, merge `c88dfffd` | thème sombre natif et palette centralisée intégrés |
| TW-117 | Réaligner la feuille de route de maintenance | Terminé | lot documentaire intégré | priorités recentrées sur installable, stabilisation et confort |
| TW-118 | Ajouter une garde des ressources runtime essentielles | Terminé | PR #184, merge `f4a3125f` | garde Linux/Windows active et chemins statiques validés |
| TW-119 | Préférences d’affichage et thème sombre optionnel | Terminé | PR #186, merge `bf48a75b` | choix Système/Clair/Sombre et échelle de police 80–200 % intégrés |
| TW-120 | Diagnostic d’installation et premier démarrage Windows | En cours | PR #187 | diagnostic autonome, intégration au paquet Windows, lanceur simple et documentation validés |

Les lots futurs doivent être confirmés par recherche dans le dépôt avant création d'une branche ou d'une PR. Ils ne constituent pas à eux seuls la preuve qu'un défaut ou un usage obsolète existe encore.

---

## Axes fonctionnels et techniques

| Domaine | Progression indicative | Prochain résultat attendu |
| --- | ---: | --- |
| Migration Python 3 / Phoenix | 92 % | valider TW-113 après consolidation documentaire finale |
| Couverture de tests automatiques | 67 % | protéger les chemins migrés et les API publiques critiques |
| Audit de compatibilité | 88 % | figer la matrice après validation de l’installable |
| Couche SQLite / encodages | 90 % | empêcher toute régression sur chemins bytes et encodages |
| Widgets wxPython | 85 % | stabiliser les composants réellement utilisés |
| Contrôles CCNS | 75 % | renforcer les cas métier spécifiques et leur traçabilité documentaire |
| Calculs de paie | 70 % | consolider les règles et exports sans prétendre remplacer un logiciel de paie |
| Exports | 72 % | fiabiliser les formats paie/comptabilité et les contrôles avant export |
| Imports | 58 % | consolider les correspondances et rejets explicites |
| Gestion du personnel | 72 % | terminer les raccords avec les écrans Teamworks existants |
| Refonte UI | 38 % | poursuivre par améliorations ciblées après stabilisation |
| Thèmes et accessibilité visuelle | 70 % | valider les préférences sur l’exécutable Windows réel |
| Performances | 20 % | mesurer avant/après sur des parcours représentatifs |
| Documentation développeur | 65 % | maintenir cette roadmap et réduire les documents contradictoires |
| Packaging Windows | 80 % | terminer TW-120 et documenter installation/mise à jour/retour arrière |
| Installation simplifiée | 65 % | diagnostic de premier démarrage et procédure testés sur poste vierge |
| Qualité / CI | 88 % | conserver uniquement des gardes pérennes et des checks fiables |

---

## Priorités consolidées

### Phase 1 — Fin de migration et stabilisation

1. valider TW-113 et geler la migration Python 3 / Phoenix ;
2. poursuivre les tests ciblés TW-112 ;
3. stabiliser les widgets réellement utilisés dans TW-110 ;
4. maintenir une CI verte et reproductible.

### Phase 2 — Version intermédiaire utilisable

1. terminer TW-120, diagnostic d’installation et premier démarrage Windows ;
2. intégrer le diagnostic et son lanceur au paquet Windows ;
3. documenter installation, mise à jour et retour arrière ;
4. valider l’exécutable sur un poste Windows vierge ;
5. conserver une version de travail avant la refonte fonctionnelle complète.

### Phase 3 — Confort et consolidation métier

1. valider les thèmes Clair/Sombre/Système et l’échelle de police sur les écrans prioritaires ;
2. stabiliser les raccords aux écrans Teamworks existants ;
3. consolider l'audit par individu et par contrat ;
4. renforcer les règles CCNS, alternance, CEE, mineurs et temps de travail ;
5. fiabiliser imports et exports.

### Phase 4 — Produit diffusable

1. modernisation mesurée de l'interface ;
2. installation simplifiée sur poste vierge ;
3. documentation utilisateur complète ;
4. procédure de migration des anciennes bases ;
5. gel Phoenix et version 1.0.

---

## Priorités de maintenance

| Priorité | Zone | Pourquoi | Première action exploitable | Critère de sortie |
| --- | --- | --- | --- | --- |
| 1 | Installation et diagnostic Windows | La version intermédiaire doit être exploitable hors environnement développeur | intégrer `tools/diagnostic_installation.py` au paquet et fournir un lanceur | rapport lisible et diagnostic exécutable sur poste vierge |
| 2 | Mesures reproductibles | Sans mesure, les optimisations risquent d'être anecdotiques | collecter les catégories existantes `connexion`, `sql`, `sql_fetch`, `transformation_python`, `widget`, `total_action` sur une base représentative | tableau avant/après joint à la PR |
| 3 | Référentiels et lectures répétées | Les relectures complètes peuvent pénaliser fiches et listes | cartographier les `SELECT *`, `fetchall()` et lectures sans filtre dans les écrans les plus utilisés | liste des requêtes priorisées par fréquence et volume |
| 4 | Service partagé CCNS | Plusieurs écrans consomment les mêmes données CCNS | définir une interface minimale de lecture contrats/classifications/grilles sans modifier les règles métier | un écran migré avec résultats identiques |
| 5 | Interface wxPython | Le rendu peut bloquer l'utilisateur, surtout à distance | mesurer remplissage, `Refresh()`, `Layout()`, `Fit()` et reconstructions complètes | réduction mesurée du temps de rendu ou justification d'abandon |
| 6 | Compatibilité dépendances | Les bibliothèques natives conditionnent Python moderne et macOS ARM | auditer `requirements.txt` avec la matrice, sans mise à jour massive | écarts documentés et lots de mise à jour séparés |
| 7 | Packaging | Le packaging doit devenir reproductible et compréhensible par un utilisateur final | finaliser l’intégration TW-120 dans les workflows Windows | paquet autonome, diagnostic et procédure cohérents |

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
