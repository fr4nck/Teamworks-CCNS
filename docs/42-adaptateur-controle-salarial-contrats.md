# TW-040 — Adaptateur du dépôt de contrats pour le contrôle salarial

`ContractRepositorySalaryControlProvider` est l'adaptateur d'infrastructure qui relie le dépôt de contrats en mémoire existant au port applicatif `ContractSalaryControlContractProvider`.

## Rôle dans l'architecture

La consultation salariale applicative reste organisée en quatre responsabilités distinctes :

1. `ContractRepository` stocke et restitue les instances existantes de `Contract` dans l'ordre déterministe du dépôt ;
2. `ContractRepositorySalaryControlProvider` sélectionne le lot demandé par le cas d'usage ;
3. `ConsultContractSalaryControlUseCase` transmet ce lot au service de consultation ;
4. le domaine salarial calcule, projette, filtre, trie et pagine les résultats métier.

L'adaptateur ne contient donc aucune règle de minimum salarial CCNS et ne déclenche aucun contrôle au démarrage.

## Règles de sélection

`list_for_salary_control()` accepte uniquement des tuples stricts de `UUID`, sans doublon :

- sans `contract_ids` ni `employee_ids`, tous les contrats du dépôt sont retournés ;
- avec `contract_ids`, seuls les contrats dont l'identifiant est demandé sont conservés ;
- avec `employee_ids`, seuls les contrats rattachés aux salariés demandés sont conservés ;
- lorsque les deux filtres sont présents, l'adaptateur applique l'intersection des critères.

Le résultat suit toujours l'ordre fourni par `ContractRepository.list_all()`. Les objets retournés sont les instances exactes de `Contract` présentes dans le dépôt. L'adaptateur ne copie pas, ne modifie pas et n'enrichit pas les contrats.

## Identifiants et frontière de conversion

Le port applicatif salarial utilise des `UUID` stricts. Le modèle historique `Contract` conserve toutefois `person_id` sous forme de chaîne et l'identifiant hérité de `Entity` est annoté comme chaîne, même si les tests salariaux manipulent déjà des `UUID`.

La frontière retenue est volontairement limitée :

- les filtres d'entrée du provider restent toujours des `UUID` stricts ;
- les contrats déjà porteurs de `UUID` sont comparés directement ;
- les chaînes historiques sont acceptées uniquement lorsqu'elles représentent explicitement un UUID valide ;
- toute autre représentation déclenche une erreur explicite.

Cette règle reprend la convention déjà présente dans le domaine salarial, sans modifier globalement le modèle historique `Contract`.

## Limites volontaires

Ce ticket n'ajoute pas de pagination, de filtre de statut, de recherche texte, de tri applicatif, d'export, d'API HTTP, d'interface graphique, d'ORM ni de second dépôt de contrats. La pagination et les autres filtres de consultation restent à la charge de la requête et des services du domaine salarial.

Aucun point de composition complet supplémentaire n'est introduit. Lorsqu'un écran, une commande ou un conteneur dédié devra exécuter ce cas d'usage, la construction attendue est : réutiliser l'instance existante de `ContractRepository`, construire `ContractRepositorySalaryControlProvider`, puis injecter ce provider dans `ConsultContractSalaryControlUseCase` avec les services de domaine salariaux déjà configurés.
