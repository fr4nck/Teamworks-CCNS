# TW-050 — Détail du contrôle salarial dans l'audit CCNS

## Objectif

L'écran d'audit CCNS affiche désormais les données déjà produites par `ContractSalaryControlController` : statut, rémunération contrôlée, minimum applicable, source du minimum et écart. L'audit ne recalcule aucun de ces éléments.

## Compatibilité de `AuditRow`

Les sept champs historiques restent dans le même ordre. Les onze champs du contrôle salarial sont ajoutés à la fin avec une valeur par défaut afin de conserver les anciens appels positionnels :

- date de référence ;
- statut et son libellé ;
- rémunération contrôlée et son libellé ;
- minimum applicable et son libellé ;
- écart et son libellé ;
- source du minimum et son libellé.

Les montants transmis par `ContractSalaryControlRowViewModel` restent des `Decimal`. Le champ historique `salaire_base` reste inchangé pour les gadgets, la synthèse individuelle et l'ancien écran d'audit.

## Base sans grille salariale

Le chemin dédié introduit par TW-049 est conservé :

- anomalie `CONTRAT_SANS_GRILLE` ;
- statut `Non évaluable` ;
- minimum et source `Non disponible` ;
- aucun montant de minimum ni aucune source inventés ;
- aucune construction de catalogue vide et aucune exécution du contrôleur.

## Écran et export

La liste wxPython conserve ses colonnes et comportements historiques, puis ajoute :

- Statut salarial ;
- Rémunération contrôlée ;
- Minimum applicable ;
- Source ;
- Écart.

Le résumé compte les contrats conformes, non conformes et non évaluables parmi les lignes filtrées. Il additionne leurs écarts directement en `Decimal`.

L'export CSV reçoit les lignes déjà chargées et filtrées. Il reprend les cinq nouveaux libellés présents dans ces lignes, sans nouvel audit, nouvelle lecture SQL ou nouveau calcul salarial.

## Vérification manuelle wxPython

À réaliser sur une base Teamworks de test :

1. ouvrir l'audit CCNS et lancer un audit comprenant au moins un contrat conforme, un non conforme et un non évaluable ;
2. vérifier les cinq nouvelles colonnes, les couleurs, le tri et l'ouverture d'un contrat ;
3. appliquer un filtre et vérifier les quatre valeurs du résumé ;
4. exporter le résultat filtré puis comparer le CSV aux valeurs affichées ;
5. recommencer sur une base sans grille et vérifier `Non évaluable` / `Non disponible`.
