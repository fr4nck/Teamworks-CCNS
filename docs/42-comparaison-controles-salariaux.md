# Comparaison des contrôles salariaux — TW-056

La comparaison de snapshots salariaux rapproche deux contrôles historisés afin d'identifier les évolutions sans recalculer les règles CCNS, les minima ou le SMIC. Elle utilise exclusivement les lignes stockées dans les snapshots TW-055.

## Snapshots comparés

Le cas d'usage reçoit deux UUID de snapshots, les charge par `ContractSalaryControlSnapshotRepository`, refuse un identifiant absent et refuse de comparer un snapshot avec lui-même. Le service de domaine est pur : il ne connaît ni repository, ni SQLite, ni wxPython, ni contrôleur salarial.

## Types de changement

Les valeurs métier stables sont en anglais : `NEW_CONTRACT`, `REMOVED_CONTRACT`, `BECAME_COMPLIANT`, `BECAME_NON_COMPLIANT`, `BECAME_NOT_EVALUATED`, `REMAINS_COMPLIANT`, `REMAINS_NON_COMPLIANT`, `REMAINS_NOT_EVALUATED`, `STATUS_CHANGED_OTHER` et `UNCHANGED`. Les libellés français sont produits uniquement par le présentateur.

## Deltas et montants

Les montants restent des `Decimal` quantifiés au centime. Pour chaque contrat, les deltas valent `après - avant`. Lorsqu'une ligne n'existe pas d'un côté, la valeur affichable est `None` et le calcul du delta utilise zéro pour le montant concerné.

## Nouveaux contrats et contrats absents

Un contrat présent uniquement dans le second snapshot est un nouveau contrat. Un contrat présent uniquement dans le premier snapshot est un contrat absent du second contrôle. Un contrat absent n'est pas considéré automatiquement comme une amélioration ou une dégradation.

## Conclusion globale

`improved` est vrai si l'écart total diminue, ou si au moins un statut devient conforme. `degraded` est vrai si l'écart total augmente, ou si un statut devient non conforme ou non évaluable. `unchanged` est vrai uniquement si aucune ligne et aucun montant total significatif ne changent.

En cas d'améliorations et de dégradations simultanées, les deux booléens `improved` et `degraded` peuvent être vrais. La présentation annonce explicitement une situation mixte au lieu de masquer une priorité implicite.

## Ordre et filtres

L'ordre est déterministe : lignes du snapshot avant dans leur ordre initial, puis nouveaux contrats dans leur ordre du snapshot après. Les filtres d'interface (tous, améliorations, dégradations, nouveaux, absents, changements de statut, écarts modifiés, inchangés) s'appliquent au résultat déjà calculé et ne déclenchent aucun accès base.

## Utilisation depuis l'historique

Le dialogue d'historique permet de sélectionner deux snapshots puis d'afficher une synthèse et le détail en lecture seule. Les limites connues sont l'absence d'export consolidé complet, réservé à TW-059, et l'absence d'ouverture enrichie du détail double lorsque l'environnement wxPython ne fournit pas de grille dédiée.
