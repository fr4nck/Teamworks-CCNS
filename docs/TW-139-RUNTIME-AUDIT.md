# TW-139 — Audit et stabilisation des parcours runtime

## Objectif

Obtenir une navigation sans traceback sur les écrans principaux de Teamworks avant toute nouvelle fonctionnalité ou refonte visuelle.

## Environnement de référence

- Windows 10 AMD64
- Python 3.11
- wxPython 4.2.5, avec préparation de la compatibilité 4.3
- base Teamworks historique existante

## Parcours de recette

| Écran | Ouverture | Chargement | Ajout | Modification | Suppression | Fermeture | Résultat |
|---|---:|---:|---:|---:|---:|---:|---|
| Accueil | ☐ | ☐ | N/A | ☐ | N/A | ☐ | À tester |
| Individus | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | À tester |
| Présences | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | À tester |
| Recrutement | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | À tester |
| Contrats | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | À tester |
| Frais | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | À tester |
| Paramètres | ☐ | ☐ | N/A | ☐ | N/A | ☐ | À tester |
| Rapports | ☐ | ☐ | N/A | ☐ | N/A | ☐ | À tester |
| Impression | ☐ | ☐ | N/A | ☐ | N/A | ☐ | À tester |

## Contrôles techniques

- imports et chargement différé des modules ;
- compatibilité wxPython 4.2.5 et 4.3 ;
- ObjectListView : largeur des colonnes, tri, filtrage, rafraîchissement ;
- dates historiques et valeurs absentes ;
- encodage UTF-8 ;
- parentage des widgets et sizers ;
- chemins runtime Windows ;
- absence de blocage de l’interface lors des chargements.

## Discipline CI

- conserver le workflow unique existant ;
- ajouter uniquement des tests ciblés et frugaux ;
- ne pas créer de nouveau workflow ;
- regrouper les correctifs issus de l’audit dans une seule PR.

## Critère de fermeture

- aucun traceback connu sur les parcours principaux ;
- tests existants au vert ;
- recette Windows renseignée ;
- aucun nouveau workflow GitHub Actions.
