# Changelog

Ce changelog distingue les corrections de la branche historique **Vanilla bug-fix** des évolutions Python 3/Phoenix, graphiques et CCNS/PMSL.

## Vanilla bug-fix PMSL — 2.1.3.1 — 27/08/2026

Base : Teamworks 2.1.3.1 d’origine, sans évolution fonctionnelle et sans migration technique.

### Corrections

- Sécurisation des sauvegardes lorsque certains répertoires sont absents.
- Sécurisation des actions sur les gadgets lorsqu’aucun élément valide n’est sélectionné.
- Sécurisation de la navigation dans l’aperçu des emails aux limites de la liste ou lorsque celle-ci est vide.
- Gestion sûre des images décoratives absentes ou invalides dans les boutons.
- Correction du contrôle de sélection dans la gestion des vacances (`GetSelection()`).
- Correction des appels `GetValue()` pour les répertoires de destination des sauvegardes.

### Périmètre conservé

- Aucun changement du schéma de base de données.
- Aucun ajout CCNS/PMSL.
- Aucune migration Python 3 / wxPython Phoenix.
- Aucun changement de thème graphique.
- Compatibilité et architecture de la branche Vanilla historique conservées.

### Traçabilité Git

- PR #298 — `Vanilla 2.1.3.1 — lot VFIX historique sûr`
- PR #299 — `Vanilla — corriger les appels GetValue de destination`

Les mêmes corrections sont reprises dans `teamworks/Versions.txt`, fichier affiché par **À propos → Notes de versions** dans Teamworks.
