# Fabrique du contrôleur de contrôle salarial

`ContractSalaryControlControllerFactory` est le point de composition applicatif dédié à la consultation du contrôle salarial des contrats. Elle centralise uniquement l’assemblage des dépendances nécessaires au contrôleur, afin qu’une future interface, commande ou vérification d’intégration n’ait pas à reconstruire manuellement toute la chaîne salariale.

## Dépendances racines attendues

La fabrique ne construit pas les dépendances qui relèvent d’une configuration externe. L’appelant fournit explicitement :

- un `ContractRepository`, déjà alimenté ou connecté au contexte applicatif concerné ;
- un `SalaryGridCatalog`, contenant les versions temporelles de grilles salariales CCNS à utiliser ;
- un `SmicCatalog`, contenant les versions temporelles du SMIC à utiliser.

La méthode `create(...)` valide strictement ces trois types. Elle ne valide pas à nouveau le contenu métier détaillé des catalogues, car cette responsabilité appartient aux modèles `SalaryGridCatalog` et `SmicCatalog`.

## Chaîne complète construite

À chaque appel, la fabrique construit une chaîne complète et neuve :

1. `ContractRepositorySalaryControlProvider` autour du repository fourni ;
2. `SalaryMinimumComplianceService` avec le catalogue CCNS fourni ;
3. `ApplicableSalaryMinimumService` avec le service de conformité et le catalogue SMIC fourni ;
4. `ContractSalaryEvaluationService` ;
5. `ContractSalaryBatchEvaluationService` ;
6. `SalaryMinimumAuditService` ;
7. `SalaryMinimumBatchAuditService` ;
8. `ContractSalaryBatchAuditService` ;
9. `ContractSalaryControlProjectionService` ;
10. `ContractSalaryControlService` ;
11. `ContractSalaryControlQueryService` ;
12. `ContractSalaryControlConsultationService` ;
13. `ConsultContractSalaryControlUseCase` ;
14. `ContractSalaryControlPresenter` ;
15. `ContractSalaryControlController`.

La construction ne lance aucune consultation. Le contrôle salarial démarre uniquement lorsque l’appelant exécute `ContractSalaryControlController.execute(...)` avec une `ContractSalaryControlControllerRequest`.

## Préservation des instances et absence d’état global

Le provider conserve l’instance exacte du `ContractRepository` fournie. Les services de calcul conservent les instances exactes de `SalaryGridCatalog` et de `SmicCatalog`. La fabrique ne copie pas ces objets, ne reconstruit pas leurs données et ne lit aucune source implicite.

La fabrique est immuable et stateless. Elle n’introduit ni singleton, ni cache global, ni variable globale mutable, ni état partagé entre deux appels. Deux appels avec les mêmes dépendances racines retournent deux contrôleurs distincts, avec des services intermédiaires distincts, tout en réutilisant les mêmes instances racines fournies par l’appelant.

## Exemple minimal

```python
from datetime import date

from application.bootstrap import ContractSalaryControlControllerFactory
from application.control import ContractSalaryControlControllerRequest
from domain.convention import (
    SalaryGridCatalog,
    create_ccns_salary_grid_2026_01,
    create_smic_catalog_2026,
)
from infrastructure.repositories import ContractRepository

contracts_repository = ContractRepository()
salary_grid_catalog = SalaryGridCatalog((create_ccns_salary_grid_2026_01(),))
smic_catalog = create_smic_catalog_2026()

controller = ContractSalaryControlControllerFactory().create(
    contracts_repository=contracts_repository,
    salary_grid_catalog=salary_grid_catalog,
    smic_catalog=smic_catalog,
)

result = controller.execute(
    ContractSalaryControlControllerRequest(reference_date=date(2026, 6, 1))
)
```

L’exemple suppose que le repository a été alimenté par l’appelant avant l’exécution si des contrats doivent être contrôlés.

## Limites volontaires

La fabrique ne fournit pas de valeurs CCNS ou SMIC par défaut, ne lit pas de fichier, ne consulte pas de variable d’environnement, n’ouvre pas de base de données et n’ajoute aucun framework d’injection de dépendances. Elle n’introduit ni route HTTP, ni serveur web, ni interface graphique, ni commande CLI, ni sérialisation JSON.
