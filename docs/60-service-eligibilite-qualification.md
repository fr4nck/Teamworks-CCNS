# Service d'éligibilité par qualification

`QualificationEligibilityService` est un service métier pur du domaine qualifications. Il compare les exigences de qualification d'une `Mission` avec les qualifications déclarées pour un `Employee`.

## Périmètre

Le service produit un résultat déclaratif `QualificationEligibilityResult` sans accès technique, sans persistance et sans consultation de date système. Il ne traite pas les équivalences, passerelles, capacités réglementaires, contrats, disponibilités, conflits de planning ou affectations automatiques.

## Règles métier

Seules les `QualificationRequirement` actives de niveau `RequirementLevel.REQUIRED` participent à l'éligibilité. Les exigences `RECOMMENDED` et `OPTIONAL`, ainsi que les exigences inactives, sont ignorées.

Une exigence REQUIRED active est satisfaite lorsqu'une `EmployeeQualification` fournie :

- appartient à l'`Employee` évalué ;
- est active ;
- porte le statut déclaré `QualificationStatus.VALID` ;
- référence la même `Qualification` que l'exigence, par identité UUID.

Le service ne compare jamais les qualifications par code ou par nom. Le statut déclaré de l'`EmployeeQualification` reste la source de vérité : aucune expiration n'est recalculée automatiquement.

## Résultat

`QualificationEligibilityResult` est immutable et expose :

- `employee` ;
- `mission` ;
- `satisfied_requirements`, tuple des exigences REQUIRED actives satisfaites ;
- `missing_requirements`, tuple des exigences REQUIRED actives manquantes.

Les méthodes `is_eligible()`, `has_missing_requirements()`, `satisfied_count()` et `missing_count()` facilitent la lecture du résultat sans ajouter de règle implicite.
