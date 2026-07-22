# TW-046 — Façade d’export du contrôle salarial

`ContractSalaryControlExporter` est la façade applicative unique pour exporter un `ContractSalaryControlViewModel` dans un format demandé par une interface ou une intégration. Elle appartient à `application.presentation` et reste indépendante de Flask, Django, FastAPI, wxPython, Qt, Tkinter ou de tout autre framework.

## Rôle de la façade

La façade centralise la sélection du format avec l’énumération stricte `ContractSalaryControlExportFormat` :

- `ContractSalaryControlExportFormat.CSV`, valeur brute `"csv"` ;
- `ContractSalaryControlExportFormat.JSON`, valeur brute `"json"`.

Elle valide strictement le view model et le format reçus, délègue à l’exporteur spécialisé correspondant, puis adapte le résultat vers un `ContractSalaryControlExport` générique et immuable.

## Différence avec les exporteurs spécialisés

Les exporteurs spécialisés restent responsables du contenu exact de chaque format :

- `ContractSalaryControlCsvExporter` produit le CSV, son nom de fichier suggéré et le MIME type CSV ;
- `ContractSalaryControlJsonExporter` produit le JSON, son nom de fichier suggéré et le MIME type JSON.

La façade ne recalcule aucune donnée métier, ne modifie ni le contenu, ni `suggested_filename`, ni `mime_type`, et ne choisit pas de MIME type global. Elle ne fait qu’orchestrer la délégation selon le format demandé.

## Absences de dépendances externes

La façade utilise uniquement la bibliothèque standard Python. Elle ne consulte aucun repository, ne lance aucun cas d’usage, ne dépend d’aucun contrôleur et ne crée aucun fichier sur disque. L’écriture, le téléchargement ou l’affichage du résultat restent sous la responsabilité de l’interface appelante.

## Exemple minimal

```python
from application.presentation import (
    ContractSalaryControlExporter,
    ContractSalaryControlExportFormat,
)

export = ContractSalaryControlExporter().export(
    view_model,
    ContractSalaryControlExportFormat.CSV,
)

print(export.suggested_filename)
print(export.mime_type)
print(export.content)
```
