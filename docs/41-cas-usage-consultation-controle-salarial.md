# TW-039 — Cas d’usage applicatif de consultation du contrôle salarial

## Rôle du cas d’usage

Le cas d’usage `ConsultContractSalaryControlUseCase` fournit un point d’entrée applicatif stable pour consulter le contrôle salarial CCNS. Il est destiné aux futures interfaces graphiques, commandes ou API qui doivent demander une consultation sans dépendre de l’organisation interne du domaine salarial.

L’entrée applicative est portée par `ConsultContractSalaryControlQuery`. Elle regroupe la date de référence, le territoire SMIC de secours optionnel, les identifiants de contrats ou de salariés à sélectionner, les statuts recherchés, la recherche textuelle, les bornes de manque salarial, le tri et la pagination.

## Chaîne de traitement

La chaîne volontairement courte est la suivante :

1. le cas d’usage reçoit une `ConsultContractSalaryControlQuery` immuable ;
2. il demande au `ContractSalaryControlContractProvider` le lot de contrats concerné par les identifiants fournis ;
3. il transforme la requête applicative en `ContractSalaryControlQuery` du domaine ;
4. il appelle une seule fois `ContractSalaryControlConsultationService.consult(...)` avec les contrats, la date, la requête de domaine et le territoire optionnel ;
5. il transforme le résultat du domaine en `ContractSalaryControlConsultationApplicationResult` immuable.

Le lot retourné par le fournisseur est transmis directement au service de domaine. Le cas d’usage ne le parcourt pas pour éviter une matérialisation ou une consommation redondante.

## Séparation entre application et domaine

La couche applicative orchestre la sélection et la délégation. Elle ne recalcule aucun minimum salarial, audit, statut, filtre, tri, compteur, pagination ou montant.

Ces responsabilités restent dans le domaine :

- `ContractSalaryControlConsultationService` produit le résultat composite de consultation ;
- `ContractSalaryControlService` produit le contrôle global ;
- `ContractSalaryControlQueryService` applique les filtres, le tri et la pagination ;
- les objets de projection du domaine portent les lignes et montants calculés.

La validation applicative est limitée aux types strictement nécessaires à la cohérence de l’entrée : date stricte, UUID stricts, enums existantes, `Decimal` strict et paramètres de pagination typés. Les validations métier déjà portées par `ContractSalaryControlQuery` ne sont pas dupliquées : la requête de domaine reste l’autorité pour les règles détaillées de filtrage et pagination.

## Validité globale et validité filtrée

Le résultat applicatif expose explicitement deux validités distinctes :

- `global_valid` provient de `ContractSalaryControlResult.valid` et décrit le contrôle complet avant filtrage ;
- `filtered_valid` provient de `ContractSalaryControlConsultationResult.valid` et décrit uniquement la consultation filtrée.

Cette distinction permet par exemple d’afficher une page filtrée conforme tout en conservant l’information qu’un autre contrat du lot global reste non conforme ou non évaluable.

## Limites volontaires du ticket

TW-039 n’ajoute pas de persistance concrète, d’ORM, d’API HTTP, d’interface graphique, ni d’export CSV/PDF.

Le port `ContractSalaryControlContractProvider` est une abstraction minimale. Il décrit uniquement la capacité nécessaire au cas d’usage : fournir les contrats à contrôler à partir d’éventuels identifiants de contrats ou de salariés. Les adaptateurs techniques seront ajoutés dans des tickets ultérieurs selon les besoins réels des interfaces ou commandes.
