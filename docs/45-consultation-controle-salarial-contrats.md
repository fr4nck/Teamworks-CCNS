# Consultation directe du contrôle salarial depuis les contrats

`ContractSalaryControlConsultationService` est le point d'entrée de domaine pour les couches qui disposent directement d'un lot de `Contract` et veulent obtenir, en une seule opération, le contrôle salarial complet et la page consultée.

La chaîne reste strictement la chaîne existante :

1. les contrats sont transmis à `ContractSalaryControlService.control(...)` avec la date de référence et le territoire de secours éventuel ;
2. le service de contrôle produit un `ContractSalaryControlResult` et sa `ContractSalaryControlProjection` ;
3. cette projection est transmise telle quelle à `ContractSalaryControlQueryService.execute(...)` avec la requête reçue ;
4. la page obtenue est associée au résultat de contrôle dans un `ContractSalaryControlConsultationResult`.

Le service ne remplace aucun moteur métier. Il ne recalcule ni évaluation salariale, ni audit, ni projection, ni filtre, ni tri, ni pagination. Il orchestre uniquement les deux services existants et propage leurs erreurs techniques.

## Résultat composite

`ContractSalaryControlConsultationResult` conserve par identité le `ContractSalaryControlResult` et la `ContractSalaryControlPage` retournés. Ses propriétés de consultation (`rows`, `filtered_rows`, compteurs filtrés, pagination, `total_shortfall_amount`, `valid`, recherches par contrat, salarié ou statut) délèguent à la page. Sa date de référence et la projection source exposent le contrôle réalisé.

La validité globale du contrôle et la validité filtrée ne doivent pas être confondues :

- `control_result.valid` décrit tout le lot contrôlé ;
- `ContractSalaryControlConsultationResult.valid` décrit seulement les lignes filtrées de la page.

Une requête peut donc filtrer toutes les lignes non conformes ou toutes les lignes d'un lot et produire une consultation filtrée valide et vide, sans modifier l'état global du contrôle.

## Identités et cohérence

Le résultat composite vérifie que `page.source_projection` est exactement `control_result.projection`, que les lignes filtrées viennent de cette projection, que les lignes retournées viennent des lignes filtrées et que l'ordre retourné correspond à la pagination. Les instances de lignes sont conservées : aucune projection, ligne ou page n'est reconstruite pour masquer une incohérence.

Les UUID sont stricts et les dataclasses sont immuables avec `slots`, comme les autres résultats de contrôle salarial.

## Itérables et territoire

Le service ne matérialise pas l'`Iterable[Contract]` reçu. Il le transmet directement au service de contrôle, ce qui permet à la chaîne complète de consommer un générateur une seule fois.

Le territoire reste uniquement un territoire de secours explicite. `None` est accepté et aucun territoire implicite n'est inventé. Lorsqu'un `SmicTerritory` est fourni, il est transmis sans transformation au contrôle existant.

## Limites volontaires

Cette orchestration ne crée aucune persistance, aucun repository, aucune API HTTP, aucune interface graphique, aucun export, aucun cache et aucune pagination SQL. Elle prépare simplement un usage futur par une couche applicative ou une interface qui souhaite consulter directement le contrôle salarial depuis un lot de contrats déjà disponible.
