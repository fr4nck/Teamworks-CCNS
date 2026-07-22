# TW-052 — Fiche de détail d'un contrôle salarial

## Rôle

La fiche de détail permet de consulter, depuis une ligne de l'audit CCNS, le résultat salarial déjà calculé pour le contrat sélectionné. Elle complète les colonnes synthétiques de l'audit sans modifier les règles CCNS, SMIC ou les données Teamworks.

## Accès depuis l'audit

Dans la liste d'audit CCNS, l'utilisateur sélectionne une ligne puis utilise le bouton **Détail salarial**. Le double-clic sur une ligne ouvre également ce détail salarial, conformément à l'usage de consultation directe dans cette liste. Si la ligne ne porte aucun résultat salarial, l'action est désactivée lorsque la sélection est connue et un message explicite est prévu pour le cas d'appel direct.

## Données affichées

La fiche est en lecture seule et regroupe :

- l'identifiant salarié, l'identifiant contrat et la date de référence ;
- la classification CCNS, la rémunération mensuelle brute contrôlée, le minimum applicable, la source du minimum, le territoire et l'écart salarial ;
- le statut, le libellé du statut, le code et le message d'anomalie éventuels, le motif de non-évaluation éventuel et le message métier disponible.

Les valeurs brutes restent conservées dans `ContractSalaryControlDetailViewModel` avec leurs types d'origine : `UUID`, `date`, `Decimal`, `Enum` et `Optional`. Les libellés servent uniquement à l'affichage.

## Statuts possibles

- **Conforme** : rémunération, minimum, source et écart nul sont affichés sans anomalie artificielle.
- **Non conforme** : l'écart exact, le code d'anomalie et le message métier issus du contrôle calculé sont affichés.
- **Non évaluable** : le motif et le message métier sont affichés avec les valeurs disponibles ; aucun minimum, source ou écart métier indisponible n'est inventé.

## Absence de recalcul

La fiche est construite par un présentateur pur à partir de la `ContractSalaryControlRowViewModel` déjà attachée à `AuditRow`. Elle n'appelle ni repository, ni contrôleur salarial, ni base de données, et ne relance pas l'audit.

## Limites de vérification graphique automatisée

Les tests automatisés couvrent le modèle, le présentateur, la conservation de la référence salariale et le comportement sans détail. La vérification wxPython complète reste manuelle lorsque wxPython n'est pas disponible dans l'environnement CI : ouvrir un audit avec un contrat conforme, un non conforme et un non évaluable, puis contrôler l'ouverture et la lisibilité de la fiche pour chaque statut.
