# Audit ciblé des performances Teamworks-CCNS

## Méthodologie

L'audit a été réalisé en lecture de code, sans modification métier, avec une recherche ciblée des accès aux données et des chemins wxPython susceptibles de bloquer l'interface :

- recherche des appels `GestionDB.DB()`, `ExecuterReq()`, `ResultatReq()`, `fetchall()`, `SELECT *`, `Layout()`, `Refresh()`, `EVT_PAINT`, `EVT_SIZE` et `EVT_IDLE` ;
- inspection prioritaire des modules CCNS, de l'accueil, des listes ObjectListView, des fiches contrat/personne et des pages de planning ;
- distinction entre lenteur de connexion, temps SQL, transformation Python et mise à jour de widgets ;
- conservation stricte des règles métier et des calculs CCNS.

Les mesures ajoutées sont désactivées par défaut. Elles s'activent avec :

```bash
TEAMWORKS_PERF_DIAG=1
```

Les mesures sont conservées uniquement en mémoire via `teamworks.Utils.UTILS_Diagnostic_performance.obtenir_mesures()`.

## Cartographie des principaux chemins d'accès aux données

| Chemin utilisateur | Modules inspectés | Accès aux données | Risque de lenteur |
| --- | --- | --- | --- |
| Démarrage / accueil | `teamworks/Ctrl/CTRL_Accueil.py`, `teamworks/Ctrl/CTRL_Gadget_CCNS.py`, `teamworks/CcnsCore/home_gadgets_ccns.py` | `GestionDB.DB()`, audit CCNS, gadgets | Chargement initial bloquant, audit volumineux |
| Audit CCNS | `teamworks/CcnsCore/audit_contracts_ccns.py`, `teamworks/Ol/OL_CCNS_audit.py` | jointure contrats/individus/classifications/types + grille salariale | lecture de nombreux contrats, transformations Python |
| Ouverture fiche contrat | `teamworks/Ctrl/CTRL_Page_contrats.py`, pages de création/édition contrat | tables contrats, types, classifications, valeurs de point | plusieurs `SELECT *` et chargements de référentiels |
| Ouverture fiche personne | `teamworks/Ctrl/CTRL_Page_generalites.py`, `teamworks/Ctrl/CTRL_Personnes.py`, `teamworks/Ol/OL_personnes.py` | coordonnées, villes, départements, régions, situations | chargement complet de tables de référence |
| Listes | `teamworks/Ol/*`, `teamworks/Ctrl/CTRL_ObjectListView.py` | requêtes de liste + reconstruction des objets | `fetchall()` et reconstruction complète de listes |
| Planning / calendriers | `teamworks/Ctrl/CTRL_Planning.py`, `teamworks/Ctrl/CTRL_Calendrier.py`, `teamworks/Ctrl/CTRL_Calendrier_tw.py` | vacances, jours fériés, présences | requêtes répétées et traitements graphiques fréquents |
| Persistance historique | `teamworks/GestionDB.py` | SQLite local ou MySQL réseau | ouverture/fermeture répétée, temps SQL non visible |

## Classement des 10 ralentissements les plus probables

| Rang | Fichier / fonction | Mécanisme | Estimation | Optimisation proposée | Impact | Fréquence | Complexité | Risque | Mesure avant/après |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `teamworks/GestionDB.py` / `DB.__init__`, `ExecuterReq`, `ResultatReq` | aucune mesure centrale du coût connexion/SQL/fetch, donc les lenteurs réseau sont invisibles | 1 ouverture + N requêtes par action | instrumentation légère désactivée par défaut | élevé | très fréquente | faible | faible | comparer catégories `connexion`, `sql`, `sql_fetch` |
| 2 | `teamworks/CcnsCore/audit_contracts_ccns.py` / `audit_contracts` | audit complet des contrats, transformations Python ligne par ligne | 1 requête contrats + 2 requêtes grille + O(n) contrôles | mesurer SQL et transformation, conserver `LIMIT`, calculer la date de référence une seule fois | élevé | accueil/audit | faible | faible | durée `accueil_ccns.audit_contracts` et totale |
| 3 | `teamworks/Ctrl/CTRL_Gadget_CCNS.py` / `MAJ` | suppression puis reconstruction complète des deux listes wx | O(stats + alertes) opérations widget | mesurer séparément vidage/remplissage, envisager gel/dégel ou diff partiel plus tard | moyen | accueil/refresh | faible | faible | durée `widget` |
| 4 | `teamworks/Ctrl/CTRL_Page_generalites.py` / chargement géographie | lecture complète villes/départements/régions | `SELECT ville, cp FROM villes` potentiellement volumineux | cache mémoire de référentiel ou recherche SQL ciblée | élevé | ouverture fiche personne | moyen | moyen | compter lignes fetchées et temps SQL |
| 5 | `teamworks/Ctrl/CTRL_Page_generalites.py` / coordonnées | requête construite par interpolation | 1 requête par fiche | paramétrer et limiter colonnes utiles | moyen | fiche personne | faible | faible | comparer temps SQL et résultat |
| 6 | `teamworks/Ctrl/CTRL_Planning.py`, `CTRL_Calendrier*.py` | `SELECT *` sur vacances/jours fériés et appels depuis vues graphiques | plusieurs requêtes par ouverture/rafraîchissement | sélectionner colonnes utiles, cache court des jours fériés/vacances | moyen | planning/calendrier | faible à moyen | faible | nombre de requêtes par ouverture |
| 7 | `teamworks/Ctrl/CTRL_ObjectListView.py` / rafraîchissements | `Refresh()`, `Layout()` et reconstruction complète de listes | O(n) widgets/objets par filtre | différer rafraîchissements successifs, ne recharger que si filtre changé | moyen | listes/recherche | moyen | moyen | durée widget + nombre d'appels MAJ |
| 8 | `teamworks/Ol/OL_*` | listes historiques avec `fetchall()` et objets complets | O(n) mémoire par liste | pousser filtres en SQL, ajouter `LIMIT` explicite sur recherches | élevé si gros volume | listes | moyen | moyen | volume lignes fetchées |
| 9 | `teamworks/Ctrl/CTRL_Creation_contrat_p3.py`, `CTRL_Creation_modele_contrat_p1.py` | plusieurs `SELECT *` de référentiels contrat | 3 requêtes par assistant | colonnes utiles + cache référentiel invalidable | faible à moyen | création contrat | faible | faible | nombre de requêtes par assistant |
| 10 | imports et modules réseau/email | imports coûteux au démarrage possible | dépend environnement | différer imports non nécessaires au démarrage | moyen | démarrage | moyen | moyen | profil import time |

## Mesures disponibles

Le module `teamworks/Utils/UTILS_Diagnostic_performance.py` fournit :

- `connexion` : ouverture SQLite/MySQL dans `GestionDB.DB.__init__` ;
- `sql` : exécution SQL dans `GestionDB.ExecuterReq` et appel d'audit CCNS depuis l'accueil ;
- `sql_fetch` : récupération des résultats dans `GestionDB.ResultatReq` ;
- `transformation_python` : construction des statistiques et alertes d'accueil CCNS ;
- `widget` : vidage et remplissage des listes du gadget CCNS ;
- `total_action` : durée complète de `build_ccns_home_data` et `CTRL_Gadget_CCNS.MAJ`.

Aucune journalisation permanente n'est ajoutée. Sans `TEAMWORKS_PERF_DIAG=1`, les mesures ne sont pas enregistrées.

## Optimisations réalisées dans cette passe

1. Ajout d'une instrumentation centrale légère, activable par variable d'environnement.
2. Instrumentation des ouvertures de connexion, exécutions SQL et `fetchall()` dans `GestionDB`.
3. Instrumentation de l'accueil CCNS pour séparer audit SQL, transformation Python et durée totale.
4. Instrumentation du gadget CCNS pour séparer vidage/remplissage des widgets et durée totale.
5. Micro-optimisation de `audit_contracts` : la date de référence CCNS et la liste des contrôles simples ne sont plus recalculées à chaque contrat.

## Optimisations recommandées pour une passe ultérieure

- Mettre en cache court les référentiels peu volatils : villes, régions, jours fériés, vacances, classifications, types de contrats.
- Réduire progressivement les `SELECT *` sur les écrans les plus utilisés.
- Ajouter des points d'injection de connexion pour regrouper plusieurs lectures dans une même unité de travail.
- Ajouter des limites SQL explicites aux listes de recherche volumineuses.
- Instrumenter les principales listes `OL_*` et les pages contrat/personne avant toute optimisation intrusive.
- Évaluer des index uniquement après mesure : par exemple colonnes utilisées dans `WHERE`, `JOIN`, `ORDER BY` des contrats, individus, coordonnées et présences. Aucune migration d'index n'est appliquée dans cette passe.

## Risques identifiés

- L'application historique mélange accès aux données, logique écran et widgets : les corrections doivent rester petites et réversibles.
- Les environnements réseau MySQL peuvent amplifier le coût des ouvertures de connexion ; les mesures doivent être prises sur un poste réel.
- Les caches de référentiels nécessitent une invalidation explicite lors des modifications de paramétrage.
- Les optimisations wxPython doivent éviter de modifier l'ordre d'affichage ou les sélections existantes.
