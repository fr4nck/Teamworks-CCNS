# Plan d'optimisation performances Teamworks-CCNS

## Lot 1 — gains rapides

| Ordre | Fichiers concernés | Correctif | Bénéfice attendu | Risques | Tests nécessaires |
| --- | --- | --- | --- | --- | --- |
| 1 | `teamworks/Utils/UTILS_Diagnostic_performance.py`, `teamworks/GestionDB.py` | conserver et exploiter les mesures connexion/SQL/fetch | identifier les actions lentes sans logs permanents | très faible | activation/désactivation, catégories collectées |
| 2 | `teamworks/CcnsCore/audit_contracts_ccns.py` | éviter les recalculs constants dans la boucle d'audit | réduire le coût Python sur gros volume | très faible | identité des résultats d'audit |
| 3 | `teamworks/Ctrl/CTRL_Gadget_CCNS.py` | mesurer séparément vidage et remplissage wx | localiser les blocages de refresh | faible | absence de double chargement, même contenu affiché |
| 4 | `teamworks/Ctrl/CTRL_Creation_contrat_p3.py`, `teamworks/Ctrl/CTRL_Creation_modele_contrat_p1.py` | remplacer les `SELECT *` référentiels par colonnes utiles | réduire volume transféré | faible | comparaison listes avant/après |

## Pré-requis avant changement de stratégie de connexion

Avant de modifier `GestionDB` ou d'introduire une connexion plus longue, comparer sur base représentative :

| Stratégie | À mesurer | Point de vigilance |
| --- | --- | --- |
| Connexion par opération | coût d'ouverture, durée SQL/fetch, erreurs | simple mais potentiellement coûteux sur réseau |
| Connexion réutilisée pendant une action | gain sur une fiche, un audit ou un assistant | option à privilégier en premier si le gain est mesuré |
| Connexion conservée pendant la vie d'un écran | gain sur refreshs successifs | risque de connexion périmée et de verrou prolongé |
| Connexion globale application | gain démarrage/actions | ne pas retenir sans test concurrence, perte réseau et fermeture propre |

Cette comparaison doit identifier le moteur réel utilisé, la gestion des transactions, le comportement concurrent, le coût d'ouverture, les verrouillages et les pertes réseau.

## Lot 2 — accès aux données

| Ordre | Fichiers concernés | Correctif | Bénéfice attendu | Risques | Tests nécessaires |
| --- | --- | --- | --- | --- | --- |
| 1 | `teamworks/Ctrl/CTRL_Page_generalites.py` | cache court ou module de référentiel géographique | éviter la relecture complète villes/départements/régions à chaque fiche | moyen : invalidation | nombre de requêtes, recherche ville identique |
| 2 | `teamworks/Ctrl/CTRL_Planning.py`, `teamworks/Ctrl/CTRL_Calendrier.py`, `teamworks/Ctrl/CTRL_Calendrier_tw.py` | cache vacances/jours fériés + colonnes utiles | diminuer les requêtes répétées lors des changements de vue | faible à moyen | nombre de requêtes par ouverture planning |
| 3 | `teamworks/Ol/OL_personnes.py`, `teamworks/Ol/OL_contrats.py` | pousser filtres/recherches en SQL, ajouter `LIMIT` quand l'écran le permet | réduire `fetchall()` volumineux | moyen | identité des filtres, ordre des résultats |
| 4 | `teamworks/GestionDB.py` et services appelants | réutiliser une connexion dans une unité de travail ciblée | réduire coût réseau et fichiers | moyen | fermeture correcte, erreurs, absence de fuite |

### Index SQL proposés mais non appliqués

Aucun index n'est ajouté automatiquement. Les candidats doivent être validés après mesure sur base réelle :

- `contrats.IDpersonne` si les fiches personne chargent régulièrement leurs contrats avec `WHERE IDpersonne = ?` ;
- `coordonnees.IDpersonne` pour l'ouverture de fiche personne ;
- colonnes date des présences/plannings uniquement si elles sont utilisées dans des `WHERE` ou `ORDER BY` mesurés.

Chaque index devra être comparé aux index existants et son coût d'écriture/stockage documenté avant migration.

## Lot 3 — accès distants et grandes listes

| Ordre | Fichiers concernés | Correctif | Bénéfice attendu | Risques | Tests nécessaires |
| --- | --- | --- | --- | --- | --- |
| 1 | `teamworks/Ol/*`, `teamworks/Ctrl/CTRL_ObjectListView.py` | mesurer lignes visibles, lignes chargées, volume transféré et temps de rendu | savoir si le problème vient de la base ou de wxPython | faible | liste de grande taille en local, réseau et bureau distant |
| 2 | listes volumineuses prioritaires | chargement par pages ou par lots si la liste dépasse les lignes visibles | réduire temps d'affichage initial | moyen : navigation, tri, filtres | identité des tris/filtres, affichage première page |
| 3 | écrans avec images/icônes | mesurer coût des icônes, images et redimensionnements | réduire latence en bureau distant | faible à moyen | mesure avec et sans images, rendu identique |
| 4 | refreshs complets | éviter reconstructions complètes lorsque filtre/tri/sélection n'a pas changé | diminuer blocage du fil graphique | moyen | nombre de `Refresh()`/`Layout()`/`Fit()` par action |

## Lot 4 — interface

| Ordre | Fichiers concernés | Correctif | Bénéfice attendu | Risques | Tests nécessaires |
| --- | --- | --- | --- | --- | --- |
| 1 | `teamworks/Ctrl/CTRL_Gadget_CCNS.py` | geler/dégeler la liste pendant remplissage, puis rafraîchir une seule fois | réduire scintillement et blocage graphique | faible | même sélection, même contenu |
| 2 | `teamworks/Ctrl/CTRL_ObjectListView.py` | regrouper `Layout()`/`Refresh()` successifs | réduire les recalculs wx | moyen | tests manuels listes/filtres |
| 3 | `teamworks/Ctrl/CTRL_Page_contrats.py`, `teamworks/Ctrl/CTRL_Page_generalites.py` | différer les blocs secondaires après affichage initial | améliorer temps perçu d'ouverture fiche | moyen | écran initial complet, chargement différé visible |
| 4 | `teamworks/Ctrl/CTRL_Planning.py` | éviter traitements lourds dans événements graphiques fréquents | réduire blocages lors redimensionnement/peinture | moyen | tests wx manuels, mesure widget |

## Ordre recommandé global

1. Déployer l'instrumentation et collecter des mesures sur une base représentative.
2. Identifier le moteur réel et comparer les quatre stratégies de connexion avant toute connexion globale.
3. Appliquer les gains rapides avec tests unitaires.
4. Prioriser le référentiel géographique et les référentiels planning si les mesures confirment leur poids.
5. Traiter les listes volumineuses avec limites/filtres SQL, pagination ou chargement par lots selon les mesures.
6. Optimiser les rafraîchissements wxPython uniquement après identification des écrans les plus coûteux.
