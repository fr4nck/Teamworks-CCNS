# Qt - Adoption du moteur documentaire

Date : 2026-10-28
Base : d2bdebf92315d2873121710ae56ec35ac4d869ae
Branche : qt/integration-document-core

## Perimetre

- Adoption selective du coeur documentaire V1.
- Conservation des API documentaires de qt/master.
- Ajout des exports du modele, des champs et du rendu HTML.
- Compatibilite MergeContext.from_mapping.
- Import TWD historique en lecture seule.
- Comparaison structurelle des fichiers TWD.
- Reprise des tests et fixtures TWD historiques.
- Reprise du prototype independant d'editeur Qt.

## Qualification locale

- Compilation Python : PASS
- Imports et smoke test : PASS
- Tests du nouveau moteur : exit 0
- Non-regression documentaire : exit 0
- Les tests Qt peuvent etre ignores si PySide6 est absent.

## Limites

- Pas encore de raccordement au dialogue documentaire Qt de production.
- Pas de generation Word ou LibreOffice.
- Pas de qualification complete de l'application Windows.
- CI GitHub a executer apres publication.
- wx/master n'est pas modifiee.