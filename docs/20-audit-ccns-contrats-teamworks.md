# Audit CCNS des contrats Teamworks

Cette étape ajoute un premier audit exploitable sur les contrats déjà présents dans Teamworks.

## Fichiers ajoutés

- `teamworks/CcnsCore/audit_contracts_ccns.py`
- `teamworks/Dlg/DLG_CCNS_audit.py`
- `teamworks/CcnsCore/menu_audit_integration.txt`

## Ce que fait l'audit

- relit les contrats historiques ;
- récupère :
  - type de contrat ;
  - classification ;
  - salaire de base ;
  - temps hebdomadaire ;
  - prime d'ancienneté ;
- applique les premiers contrôles déjà codés :
  - classification présente ;
  - grille présente ;
  - minimum depuis la grille ;
  - ancienneté standard.

## Pourquoi c'est rentable

Après le seed et le raccord au vrai dépôt, c'est la manière la plus rapide de rendre le travail utile sur des données réelles.
