# Ouverture de la fiche contrat depuis l'audit

Cette étape ajoute un accès direct à la fiche contrat depuis la liste d'audit CCNS.

## Ce que ça apporte

- bouton **Ouvrir le contrat**
- double-clic sur la ligne
- tentative d'ouverture de la fiche contrat existante Teamworks
- message propre si l'environnement exact ne permet pas l'ouverture directe

## Pourquoi c'est utile

L'audit ne reste plus une liste isolée :
on peut passer du contrôle à la fiche contrat presque immédiatement.

## Remarque

L'intégration reste défensive :
le code tente d'utiliser les points d'entrée déjà présents dans `CTRL_Page_contrats.py` sans imposer un refactoring lourd.
