# TW-045 — Export JSON du contrôle salarial

`ContractSalaryControlJsonExporter` transforme un `ContractSalaryControlViewModel` déjà construit en document JSON stable pour une future interface web, une API ou une intégration externe. Il appartient à la couche `application.presentation` et travaille uniquement sur le modèle de présentation reçu.

## Structure du document

Le document contient des sections explicitement ordonnées :

- `reference_date` et `status` pour identifier la consultation et son état de présentation brut ;
- `summary` pour les libellés d'affichage de synthèse (`title`, `message`) ;
- `validity`, `counts` et `amounts` pour les agrégats déjà présents dans le ViewModel ;
- `pagination` pour l'intégralité des informations de page exportables ;
- `empty_state`, à `null` ou avec ses libellés d'affichage ;
- `rows`, tableau ordonné des lignes du ViewModel.

Chaque ligne expose les identifiants, la date de référence, le statut, la classification, les montants, la source du minimum, le territoire, les raisons d'échec et les anomalies sous forme de valeurs sérialisables.

## Règles de conversion

L'exporteur utilise uniquement la bibliothèque standard Python et convertit explicitement les types non JSON natifs :

- `date` devient une chaîne ISO 8601 `YYYY-MM-DD` ;
- `UUID` devient sa chaîne canonique ;
- `Enum` devient sa valeur brute (`value`) et jamais le nom Python ;
- `Decimal` devient une chaîne décimale exacte, sans conversion en `float` ;
- `None` devient `null` ;
- les booléens restent des booléens JSON ;
- le tuple `rows` devient un tableau JSON dans le même ordre.

Le JSON est indenté, déterministe, généré avec `ensure_ascii=False` pour conserver les accents français, et terminé par un saut de ligne. L'ordre des clés est défini par l'exporteur plutôt que par un tri implicite.

## Valeurs brutes et libellés

Les champs techniques privilégient les valeurs brutes disponibles dans le ViewModel : statuts, sources, territoires et raisons d'échec sont exportés avec leurs valeurs d'enum. Les libellés français restent réservés aux zones d'affichage comme `summary` et `empty_state`, afin que les intégrations externes puissent consommer des valeurs stables indépendantes de la langue de l'interface.

## Absences volontaires

L'exporteur ne lance aucun calcul salarial, n'appelle ni repository, ni cas d'usage, ni contrôleur, ni présentateur. Il ne crée et ne modifie aucun fichier : il retourne seulement un contenu JSON, un nom de fichier suggéré déterministe `controle-salarial-YYYY-MM-DD.json` et le MIME type `application/json; charset=utf-8`.

## Exemple minimal

```python
from application.presentation import ContractSalaryControlJsonExporter

export = ContractSalaryControlJsonExporter().export(view_model)
print(export.suggested_filename)
print(export.mime_type)
print(export.content)
```
