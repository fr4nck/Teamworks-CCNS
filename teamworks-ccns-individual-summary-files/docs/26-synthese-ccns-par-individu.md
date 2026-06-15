# Synthèse CCNS par individu

Cette étape prépare le vrai écran de contrôle par personne dans Teamworks.

## Fichiers ajoutés

- `teamworks/CcnsCore/audit_person_summary.py`
- `teamworks/Ctrl/CTRL_Page_ccns_synthese.py`
- `teamworks/Dlg/DLG_Fiche_individuelle_ccns_integration.txt`

## Ce que ça apporte

- une synthèse CCNS centrée sur l'individu ;
- un statut global :
  - Bloquant
  - A revoir
  - OK
  - Aucun contrat
- un comptage par niveau ;
- une liste des contrats de la personne ;
- ouverture directe du contrat depuis la synthèse.

## Pourquoi c'est important

Cela s'appuie sur la logique déjà présente dans Teamworks :
la fiche individuelle devient un vrai point d'entrée de contrôle, au lieu de rester seulement un écran administratif.
