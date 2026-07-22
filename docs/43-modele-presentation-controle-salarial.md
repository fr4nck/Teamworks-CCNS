# TW-041 — Modèle de présentation du contrôle salarial

## Rôle du présentateur

`ContractSalaryControlPresenter` transforme un `ContractSalaryControlConsultationApplicationResult` déjà produit par le cas d’usage de consultation en un `ContractSalaryControlViewModel` immuable. Il s’agit d’un adaptateur de présentation pur : il ne lance pas le contrôle salarial, n’interroge aucun dépôt, n’applique aucun filtre, ne modifie pas le tri et ne recalcule pas les minima.

Le modèle obtenu peut être consommé par une interface wxPython, une page web, une commande ou tout autre canal sans dépendre d’un framework d’interface.

## Séparation résultat applicatif / présentation

Le résultat applicatif conserve les valeurs issues du domaine : lignes de contrôle, compteurs, validités, manque salarial filtré et pagination. Le modèle de présentation ajoute uniquement des libellés déterministes et des informations prêtes à afficher.

Les valeurs brutes ne sont pas supprimées. Les dates restent des `date`, les montants restent des `Decimal`, les identifiants restent des `UUID` et les statuts métier restent des `ContractSalaryControlStatus` sur les lignes présentées.

## Statuts d’affichage

Le statut `ContractSalaryControlPresentationStatus` décrit uniquement la manière d’afficher le résultat :

- `EMPTY` : aucune ligne n’est retournée sur la page consultée ;
- `SUCCESS` : le résultat filtré non vide est valide et le lot global est valide ;
- `WARNING` : le résultat filtré est valide alors que le lot global est invalide, ou le résultat filtré contient uniquement des lignes non évaluables comme anomalie ;
- `ERROR` : le résultat filtré contient au moins un contrat non conforme.

Les statuts métier du domaine ne sont pas modifiés. Leurs libellés utilisateur sont stables : `COMPLIANT` devient « Conforme », `NON_COMPLIANT` devient « Non conforme » et `NOT_EVALUATED` devient « Non évaluable ».

## Formatage des montants et des dates

Les montants sont quantifiés à deux décimales avec `ROUND_HALF_UP` et formatés sans dépendre de la locale du système. Le séparateur de milliers est une espace, le séparateur décimal est une virgule et le suffixe est l’euro, par exemple « 2 099,37 € » ou « 0,00 € ». Les montants ne sont jamais convertis en `float`.

Les dates sont formatées au format numérique français déterministe `JJ/MM/AAAA`, par exemple « 01/01/2026 ». Le formatage ne dépend pas de la locale du poste ou du serveur.

## Pagination

`ContractSalaryControlPaginationViewModel` expose l’offset, la limite, les offsets précédent et suivant, les indicateurs de page précédente et suivante, le total filtré, les numéros de première et dernière lignes affichées et un libellé de plage.

Un résultat vide ou un offset supérieur ou égal au total filtré produit le libellé « Résultats 0 à 0 sur N » et ne renseigne pas de première ni de dernière ligne affichée. Une limite absente est conservée telle quelle et la plage couvre les lignes retournées à partir de l’offset.

## Validité globale et validité filtrée

La validité globale décrit l’ensemble du lot contrôlé. La validité filtrée décrit uniquement les lignes conservées par la requête applicative avant pagination. Le présentateur conserve les deux valeurs pour permettre à l’interface de signaler qu’une page filtrée peut être conforme alors que le lot global comporte encore des anomalies.

## Limites volontaires

Ce ticket n’ajoute pas d’écran HTML, de route HTTP, d’API JSON, d’export CSV ou PDF, ni de persistance. Il n’enrichit pas les lignes avec des informations absentes du résultat source, notamment les noms ou prénoms des salariés. Il ne crée pas de seconde couche applicative concurrente et ne contient aucune dépendance à un framework d’interface.
