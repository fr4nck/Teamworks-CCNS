# Couche d'accès aux données CCNS

## Pourquoi introduire cette couche

`teamworks/GestionDB.py` reste le fournisseur historique de données de Teamworks. Il est très transversal : connexion, exécution SQL, compatibilité SQLite/MySQL et usages par les écrans wxPython. Les audits de performance, de compatibilité, de pérennité et d'architecture l'identifient comme un composant critique à moderniser progressivement, sans réécriture globale.

Cette première brique isole les lectures nécessaires au moteur CCNS afin de réduire le couplage entre le domaine CCNS et les requêtes SQL historiques.

## Rôle

La classe `CcnsDataReader`, située dans `infrastructure/persistence/ccns_data_reader.py`, centralise les lectures Teamworks utilisées par l'audit CCNS :

- `lire_contrats()` ;
- `lire_classifications()` ;
- `lire_grilles()` ;
- `lire_lignes_grille()`.

Elle ouvre une connexion via `GestionDB.DB`, exécute des requêtes SQL explicites, puis convertit les tuples historiques en DTO simples définis dans `domain/repositories/ccns_data.py`.

La couche ne contient volontairement aucune règle métier CCNS, aucun calcul de minimum conventionnel et aucune logique wxPython.

## Ce qui est remplacé progressivement

L'audit `teamworks/CcnsCore/audit_contracts_ccns.py` ne construit plus directement les requêtes SQL de lecture des contrats et des grilles. Il consomme désormais un lecteur injecté ou, par défaut, `CcnsDataReader`.

Le comportement métier reste porté par le moteur existant : contrôles simples, contrôle de minimum depuis grille et contrôle d'ancienneté.

## Ce qui reste historique

Cette PR ne remplace pas `GestionDB.py` et ne modifie pas ses API. Les autres écrans et modules continuent d'utiliser les accès historiques.

`CcnsDataReader` est donc une façade progressive au-dessus de `GestionDB`, compatible avec la stratégie de migration par périmètres limités.

## Mesures et performance

Le chemin audit conserve le même volume de requêtes que l'implémentation précédente pour son besoin courant :

1. lecture des contrats ;
2. lecture de la première grille salariale ;
3. lecture des lignes de cette grille.

La connexion `GestionDB.DB()` est ouverte une seule fois par lecteur et réutilisée pour ces lectures, ce qui évite d'introduire des ouvertures supplémentaires. La nouvelle séparation améliore surtout la testabilité et prépare des mesures plus fines sans changer le comportement utilisateur.

## Prochaines étapes recommandées

1. Étendre progressivement cette couche aux autres lectures CCNS transverses identifiées par les audits.
2. Ajouter des mesures centralisées de temps SQL et temps Python autour du lecteur, désactivées par défaut.
3. Stabiliser des contrats de données plus complets pour les écrans contrats et les tableaux d'audit.
4. Introduire, uniquement si les mesures le justifient, des caches courts et invalidables pour les référentiels CCNS.
5. Préparer ensuite un dépôt persistant remplaçable afin de pouvoir substituer progressivement `GestionDB` sans effet de bord sur les écrans historiques.
