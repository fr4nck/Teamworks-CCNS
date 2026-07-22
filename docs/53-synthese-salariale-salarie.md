# TW-053 — Synthèse salariale d’un salarié

La synthèse salariale regroupe, pour un salarié identifié par son UUID stable, les lignes de contrôle salarial déjà présentes dans le résultat complet de l’audit CCNS courant. Elle permet de lire en un seul écran les contrats contrôlés, les compteurs par statut et le total des écarts, puis d’ouvrir la fiche de détail salarial TW-052 de chaque contrat.

## Accès depuis l’audit

Depuis la fenêtre d’audit CCNS, sélectionner une ligne possédant un résultat salarial et un identifiant salarié, puis utiliser l’action **Synthèse salarié**. Le bouton **Détail salarial** reste dédié à la ligne sélectionnée et le double-clic continue d’ouvrir la fiche TW-052.

## Périmètre

La synthèse utilise les lignes complètes chargées par l’audit courant, avant filtre et tri visuels. Les filtres et tris de la liste ne réduisent donc pas et ne réordonnent pas le périmètre de synthèse. Si l’audit a été lancé avec une limite ou un périmètre partiel, la synthèse indique qu’elle couvre uniquement les contrats chargés dans ce périmètre courant.

## Calculs affichés

Aucun contrôle salarial n’est relancé : les lignes `ContractSalaryControlRowViewModel` déjà attachées aux lignes d’audit sont réutilisées telles quelles.

- `total_count` compte les contrats du salarié dans le périmètre chargé.
- `compliant_count`, `non_compliant_count` et `not_evaluated_count` sont calculés uniquement à partir des statuts déjà présents.
- `total_shortfall_amount` additionne exclusivement les `shortfall_amount` existants, en `Decimal`, avec l’arrondi monétaire déjà utilisé par les présentateurs.
- `valid` vaut vrai uniquement si la synthèse n’est pas vide et qu’aucune ligne retenue n’est non conforme ou non évaluable.
- Une synthèse vide est déterministe : compteurs à zéro, total `0,00 €`, aucune lecture base et aucun recalcul automatique.

## Détail salarial

La liste des contrats conserve l’ordre d’origine des lignes d’audit chargées. Le bouton **Détail salarial** et le double-clic délèguent à `ContractSalaryControlDetailPresenter` puis au dialogue TW-052, sans dupliquer la logique de détail.

## Limites de vérification graphique

Les tests automatisés couvrent le présentateur pur, l’adaptateur depuis l’audit et l’orchestration sans dépendance wxPython lorsque l’environnement CI ne fournit pas l’interface graphique. Une vérification manuelle reste nécessaire pour valider l’ergonomie wxPython réelle, le redimensionnement et la lisibilité sur les écrans cibles.
