# Performance

Ce document définit les règles de développement relatives aux performances de Teamworks.

L'objectif est de conserver une application réactive, y compris sur des postes anciens, des réseaux lents et des environnements distants, sans modifier les règles métier.

---

# Principes

Les performances se mesurent.

Aucune optimisation importante ne doit être réalisée sans mesure préalable.

Privilégier les optimisations simples, locales, réversibles et documentées.

Les performances ne doivent jamais dégrader la lisibilité du code.

---

# Priorités

1. Exactitude fonctionnelle
2. Lisibilité
3. Simplicité
4. Performances
5. Optimisations micro

Une optimisation qui rend le code difficile à maintenir est à éviter.

---

# Accès aux données

Éviter :

- les requêtes SQL dans des boucles ;
- les schémas N+1 ;
- les lectures complètes lorsqu'un filtre SQL suffit ;
- les `SELECT *` inutiles ;
- les ouvertures répétées de connexion dans une même opération.

Privilégier :

- une requête plutôt que plusieurs identiques ;
- les requêtes paramétrées ;
- les traitements SQL lorsque cela réduit fortement les transferts ;
- la réutilisation des données déjà chargées.

Ne jamais ajouter un index sans démontrer son intérêt.

---

# Interface wxPython

Ne pas bloquer le thread graphique.

Les traitements longs doivent être :

- différés ;
- découpés ;
- ou exécutés hors du constructeur du panneau lorsque cela est possible.

Limiter :

- `Refresh()`
- `Layout()`
- `Fit()`

Éviter les reconstructions complètes lorsqu'une mise à jour partielle suffit.

---

# Cache

Le cache n'est jamais la première solution.

Avant d'ajouter un cache :

- supprimer les calculs redondants ;
- supprimer les requêtes dupliquées ;
- mesurer.

Lorsqu'un cache est nécessaire :

- durée courte ;
- invalidation explicite ;
- fonctionnement documenté ;
- aucune persistance implicite.

---

# Instrumentation

Le diagnostic des performances reste désactivé par défaut.

Les mesures doivent permettre d'isoler :

- ouverture de connexion ;
- exécution SQL ;
- récupération des données ;
- transformation Python ;
- rendu wxPython ;
- durée totale.

Les outils de mesure ne doivent pas perturber le fonctionnement normal.

---

# Contextes d'utilisation

Les optimisations doivent rester adaptées aux différents contextes :

- poste local ;
- base sur partage réseau ;
- application exécutée sur serveur ;
- bureau distant ;
- plusieurs utilisateurs.

Une optimisation valable dans un contexte peut être contre-productive dans un autre.

---

# Validation

Toute optimisation doit répondre aux questions suivantes :

- Le gain est-il mesuré ?
- Les résultats métier sont-ils identiques ?
- Le code reste-t-il lisible ?
- Les tests passent-ils ?
- Le risque de régression est-il faible ?

Si une réponse est non, l'optimisation doit être reconsidérée.

---

# Philosophie

Une amélioration de 5 % reproductible vaut mieux qu'une optimisation spectaculaire non mesurée.

Les performances de Teamworks doivent progresser en continu, par petites évolutions maîtrisées, sans remettre en cause la stabilité du logiciel.
