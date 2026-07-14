# Audit ciblé des performances Teamworks-CCNS

## Méthodologie

L'audit a été réalisé en lecture de code, sans modification métier, avec une recherche ciblée des accès aux données et des chemins wxPython susceptibles de bloquer l'interface :

- recherche des appels `GestionDB.DB()`, `ExecuterReq()`, `ResultatReq()`, `fetchall()`, `SELECT *`, `Layout()`, `Refresh()`, `EVT_PAINT`, `EVT_SIZE` et `EVT_IDLE` ;
- inspection prioritaire des modules CCNS, de l'accueil, des listes ObjectListView, des fiches contrat/personne et des pages de planning ;
- distinction entre lenteur de connexion, temps SQL, transformation Python et mise à jour de widgets ;
- distinction explicite des contextes d'exploitation : application et base locales, application sur serveur en accès distant, application locale avec base sur partage réseau, et plusieurs utilisateurs sur la même base ;
- conservation stricte des règles métier et des calculs CCNS.

Les mesures ajoutées sont désactivées par défaut. Elles s'activent avec :

```bash
TEAMWORKS_PERF_DIAG=1
```

Les mesures sont conservées uniquement en mémoire via `teamworks.Utils.UTILS_Diagnostic_performance.obtenir_mesures()`.

## Points à établir avant toute modification des connexions

Aucune conclusion ne doit supposer qu'une connexion persistante est systématiquement préférable. Avant d'intervenir sur la gestion des connexions, il faut documenter sur l'environnement réel :

1. le moteur réellement utilisé : SQLite local, SQLite sur chemin réseau, ou MySQL via `GetConnexionReseau()` ;
2. la gestion actuelle des transactions : commits explicites dans `Commit()`, commits intégrés à plusieurs méthodes d'écriture et fermeture dans `Close()` ;
3. la compatibilité avec les accès concurrents : verrouillage fichier SQLite, partage réseau, comportement MySQL, nombre d'utilisateurs simultanés ;
4. le coût réel d'ouverture d'une connexion, mesuré séparément du SQL et du `fetchall()` ;
5. les risques de verrouillage, connexion périmée, perte réseau, timeout et reconnexion ;
6. les quatre stratégies à comparer sur une action représentative : connexion par opération, connexion réutilisée pendant une action, connexion conservée pendant la durée de vie d'un écran, connexion globale à l'application.

La stratégie privilégiée pour une première passe reste la réutilisation d'une connexion dans une même unité de travail, par exemple un audit ou l'ouverture complète d'une fiche, plutôt qu'une connexion globale permanente.

## Coûts à mesurer séparément

| Coût | Mesure attendue | Pourquoi le séparer |
| --- | --- | --- |
| Ouverture de connexion | durée `connexion` par moteur, chemin local/réseau et type d'action | une ouverture lente peut venir du réseau, de MySQL, d'un partage fichier ou de l'antivirus |
| Latence application-base | durée SQL minimale sur requête simple, puis durée par requête métier | permet de distinguer latence réseau et requêtes lourdes |
| Volume transféré | nombre de lignes, colonnes utiles, taille approximative des objets Python | conditionne les usages distants et les bases partagées |
| Lectures complètes | nombre de `SELECT *`, `fetchall()` et lectures sans `WHERE`/`LIMIT` | signale les écrans qui chargent plus que nécessaire |
| Interface wxPython | temps de création, remplissage, `Layout()`, `Refresh()`, `Fit()` | sépare lenteur base et blocage graphique |
| Reconstructions de listes | nombre de suppressions/remplissages complets ObjectListView ou listes wx | identifie les refreshs évitables |
| Blocages du fil graphique | durée d'action exécutée sur le thread principal avant rendu | critique en bureau distant et sur listes volumineuses |
| Accès simultané | erreurs, attentes de verrou, conflits d'écriture, durée commit | indispensable avec plusieurs utilisateurs sur la même base |

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

## Mesures spécifiques aux usages distants

Pour une application utilisée via bureau distant ou pour une application locale accédant à une base réseau, les mesures doivent inclure :

- temps d'affichage d'une grande liste, en séparant requête SQL, transfert, transformation Python et rendu wxPython ;
- nombre de lignes réellement visibles à l'écran au premier affichage ;
- intérêt d'un chargement par pages ou par lots lorsque la liste complète dépasse les lignes visibles ;
- possibilité de charger d'abord les données visibles, puis le reste de manière différée ;
- coût des icônes, images, redimensionnements et conversions associées ;
- nombre de rafraîchissements complets évitables après filtre, tri, redimensionnement ou changement d'onglet.

## Classement des 10 ralentissements les plus probables

| Rang | Fichier / fonction | Mécanisme | Estimation | Optimisation proposée | Impact | Fréquence | Complexité | Risque | Mesure avant/après |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `teamworks/GestionDB.py` / `DB.__init__`, `ExecuterReq`, `ResultatReq` | aucune mesure centrale du coût connexion/SQL/fetch, donc les lenteurs réseau sont invisibles | 1 ouverture + N requêtes par action | instrumentation légère désactivée par défaut | élevé | très fréquente | faible | faible | comparer catégories `connexion`, `sql`, `sql_fetch` par moteur et contexte |
| 2 | `teamworks/CcnsCore/audit_contracts_ccns.py` / `audit_contracts` | audit complet des contrats, transformations Python ligne par ligne | 1 requête contrats + 2 requêtes grille + O(n) contrôles | mesurer SQL et transformation, conserver `LIMIT`, calculer la date de référence une seule fois | élevé | accueil/audit | faible | faible | durée `accueil_ccns.audit_contracts` et totale |
| 3 | `teamworks/Ctrl/CTRL_Gadget_CCNS.py` / `MAJ` | suppression puis reconstruction complète des deux listes wx | O(stats + alertes) opérations widget | mesurer séparément vidage/remplissage, envisager gel/dégel ou diff partiel plus tard | moyen | accueil/refresh | faible | faible | durée `widget` et nombre de reconstructions |
| 4 | `teamworks/Ctrl/CTRL_Page_generalites.py` / chargement géographie | lecture complète villes/départements/régions | `SELECT ville, cp FROM villes` potentiellement volumineux | cache mémoire de référentiel ou recherche SQL ciblée | élevé | ouverture fiche personne | moyen | moyen | compter lignes fetchées et temps SQL |
| 5 | `teamworks/Ctrl/CTRL_Page_generalites.py` / coordonnées | requête construite par interpolation | 1 requête par fiche | paramétrer et limiter colonnes utiles | moyen | fiche personne | faible | faible | comparer temps SQL et résultat |
| 6 | `teamworks/Ctrl/CTRL_Planning.py`, `CTRL_Calendrier*.py` | `SELECT *` sur vacances/jours fériés et appels depuis vues graphiques | plusieurs requêtes par ouverture/rafraîchissement | sélectionner colonnes utiles, cache court des jours fériés/vacances | moyen | planning/calendrier | faible à moyen | faible | nombre de requêtes par ouverture |
| 7 | `teamworks/Ctrl/CTRL_ObjectListView.py` / rafraîchissements | `Refresh()`, `Layout()`, `Fit()` et reconstruction complète de listes | O(n) widgets/objets par filtre | différer rafraîchissements successifs, ne recharger que si filtre changé | moyen | listes/recherche | moyen | moyen | durée widget + nombre d'appels MAJ |
| 8 | `teamworks/Ol/OL_*` | listes historiques avec `fetchall()` et objets complets | O(n) mémoire par liste | pousser filtres en SQL, ajouter `LIMIT` explicite sur recherches | élevé si gros volume | listes | moyen | moyen | volume lignes fetchées et lignes visibles |
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

## Recommandations par contexte d'exploitation

### Usage local : application et base sur le poste

- Prioriser la réduction des lectures complètes et des reconstructions wxPython avant une connexion globale.
- Mesurer le coût d'ouverture SQLite : s'il reste négligeable, conserver une connexion courte peut limiter les risques de fuite et de verrou.
- Regrouper les lectures d'une même action avec une connexion réutilisée seulement lorsque les mesures montrent un gain.

### Base située sur réseau ou base partagée

- Mesurer séparément latence, volume transféré, temps de verrouillage et erreurs de perte réseau.
- Éviter les `fetchall()` non bornés et préférer filtres SQL, colonnes utiles et pagination sur les listes volumineuses.
- Tester les accès concurrents en lecture et écriture avant tout cache ou connexion longue : une connexion conservée peut devenir périmée ou maintenir un verrou plus longtemps.
- Documenter le moteur exact : SQLite sur partage réseau n'a pas les mêmes garanties ni les mêmes symptômes que MySQL.

### Application utilisée en bureau distant

- Réduire d'abord le coût d'affichage : chargement initial visible, icônes, images, redimensionnements, `Refresh()`, `Layout()` et `Fit()` successifs.
- Charger les grandes listes par lots ou afficher d'abord les lignes visibles si l'expérience utilisateur est dominée par le rendu.
- Différer les calculs secondaires après l'affichage initial pour limiter les blocages du fil graphique.
- Comparer le temps perçu par l'utilisateur avec le temps SQL : en bureau distant, le rendu complet d'une liste peut coûter plus cher que la requête.

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
- Les bases SQLite sur partage réseau peuvent exposer des délais de verrouillage, des erreurs transitoires ou des pertes d'accès différentes d'un poste local.
- Les connexions longues peuvent masquer le coût d'ouverture mais introduire connexions périmées, verrous prolongés et comportements différents après perte réseau.
- Les caches de référentiels nécessitent une invalidation explicite lors des modifications de paramétrage.
- Les optimisations wxPython doivent éviter de modifier l'ordre d'affichage ou les sélections existantes.
