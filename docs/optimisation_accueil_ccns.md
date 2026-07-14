# Optimisation de l'accueil CCNS

## Cause de la lenteur

Le gadget d'accueil CCNS appelait séparément `build_ccns_home_gadgets()` puis `build_ccns_home_alert_lines()`.
Ces deux fonctions relançaient chacune `audit_contracts()`, ce qui relisait les contrats et la grille salariale deux fois pour un même affichage.
Le calcul était aussi déclenché directement pendant la construction du panneau wxPython, avant que la fenêtre ait eu la possibilité de s'afficher.

## Optimisation réalisée

La fonction centrale `build_ccns_home_data(limit=5000, max_lines=12, force_refresh=False)` construit désormais les statistiques et les lignes d'alerte à partir d'un seul appel à `audit_contracts()`.
Les fonctions historiques restent disponibles comme wrappers pour limiter l'impact sur le reste de l'application.

Le panneau `CTRL_Gadget_CCNS` affiche d'abord `Chargement…`, puis diffère le calcul avec `wx.CallAfter` afin de laisser wxPython terminer l'affichage initial. Le calcul reste exécuté sur le thread principal pour éviter toute modification dangereuse de l'interface depuis un thread secondaire.

## Cache mémoire

Un cache mémoire court, explicite et non persistant conserve les données d'accueil CCNS pendant 45 secondes par couple `(limit, max_lines)`.
Il peut être vidé avec `clear_ccns_home_cache()` ou renouvelé avec `refresh_ccns_home_data()`.
Le bouton **Actualiser** appelle la construction avec `force_refresh=True`, ce qui invalide le résultat courant et relance un audit complet.

## Mesures de performance

La durée de construction est mesurée avec `time.perf_counter()` et envoyée au logger du module en niveau `DEBUG` uniquement. La sortie normale de l'application n'est donc pas polluée.

Mesure reproductible suggérée en développement : activer le logging `DEBUG` pour `teamworks.CcnsCore.home_gadgets_ccns`, ouvrir le gadget CCNS, puis comparer :

- avant optimisation : deux audits complets pour un affichage ;
- après optimisation : un audit complet au premier affichage, puis réutilisation du cache pendant 45 secondes sauf actualisation forcée.

## Autres appels à `audit_contracts()`

Les dialogues d'audit CCNS continuent d'appeler `audit_contracts()` lorsqu'ils affichent une liste complète ou filtrée. Ces appels correspondent à des écrans dédiés à l'audit et n'ont pas été modifiés afin de rester dans le périmètre de l'optimisation de l'accueil et du gadget CCNS.
