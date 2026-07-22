# TW-042 — Contrôleur de consultation du contrôle salarial

## Rôle

`ContractSalaryControlController` fournit un point d’entrée applicatif de présentation pour les futures interfaces de consultation du contrôle salarial. Il reste indépendant des technologies d’interface : aucune route HTTP, aucun serveur web, aucun widget graphique et aucune sérialisation JSON ne sont introduits.

Le contrôleur orchestre uniquement la consultation. Il ne sélectionne pas directement les contrats, ne calcule pas de minimum salarial, ne filtre pas les lignes, ne trie pas, ne pagine pas et ne formate pas les montants.

## Chaîne d’appel

La chaîne prévue est la suivante :

```text
interface concrète
  → ContractSalaryControlControllerRequest
  → ContractSalaryControlController
  → ConsultContractSalaryControlUseCase
  → ContractSalaryControlPresenter
  → ContractSalaryControlControllerResult
```

Une interface concrète construit une `ContractSalaryControlControllerRequest` avec des types déjà applicatifs (`date`, `UUID`, `Decimal`, énumérations et tuples stricts). La conversion depuis des chaînes HTML, JSON ou CLI reste volontairement hors périmètre.

La requête contrôleur expose `to_application_query()`, qui construit une `ConsultContractSalaryControlQuery`. Les validations détaillées restent donc déléguées à la requête applicative et à la requête domaine déjà existantes.

## Erreurs utilisateur et erreurs techniques

Le contrôleur convertit uniquement les erreurs attendues de validation de requête (`TypeError` ou `ValueError`) en `ContractSalaryControlControllerError` avec un code stable, par exemple `INVALID_REFERENCE_DATE`, `INVALID_CONTRACT_IDS`, `INVALID_SHORTFALL_RANGE`, `INVALID_SORT` ou `INVALID_PAGINATION`.

Les erreurs techniques provenant du provider, du repository, du moteur salarial, d’un invariant interne ou d’une erreur de programmation ne sont pas masquées. Elles sont propagées telles quelles afin de conserver la cause originale et d’éviter qu’une panne technique soit présentée comme une simple erreur de saisie.

## Résultat immuable

`ContractSalaryControlControllerResult` distingue explicitement :

- un succès : `successful=True`, `view_model` présent, `errors=()` ;
- un échec attendu : `successful=False`, `view_model=None`, `errors` non vide.

Les invariants refusent les résultats ambigus. Les modèles de requête, de résultat et d’erreur sont immuables.

## Pagination

Le contrôleur est sans état interne. Il ne mémorise donc aucun offset courant.

Lorsqu’un filtre ou un tri change, une interface peut appeler `ContractSalaryControlControllerRequest.first_page()`. Cette méthode pure retourne une nouvelle requête identique avec `offset=0` sans modifier l’instance existante.

## Limites volontaires du ticket

Ce ticket n’ajoute pas :

- d’adaptateur HTTP, web, CLI ou graphique ;
- de parsing de chaînes de formulaire ;
- de sérialisation JSON ;
- de repository ;
- de calcul métier ou de duplication du présentateur ;
- d’état mutable dans le contrôleur.
