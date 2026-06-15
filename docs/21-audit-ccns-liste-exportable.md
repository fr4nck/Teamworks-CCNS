# Audit CCNS en liste exportable

Cette étape remplace l'affichage texte brut par une vraie liste exploitable.

## Fichiers ajoutés

- `teamworks/Ol/OL_CCNS_audit.py`
- `teamworks/Dlg/DLG_CCNS_audit_list.py`
- `teamworks/CcnsCore/menu_audit_list_integration.txt`

## Ce que ça apporte

- affichage tabulaire des contrats audités ;
- colonnes lisibles :
  - contrat
  - nom
  - classification
  - type
  - salaire
  - anomalies
  - messages
- export CSV ;
- base plus proche d'un vrai outil de contrôle Teamworks.

## Pourquoi c'est rentable

Après l'audit brut, c'est la transformation la plus utile :
on passe d'un outil de test à un outil déjà exploitable pour relire et trier des contrats.
