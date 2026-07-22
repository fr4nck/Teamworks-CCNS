# TW-047 — Contrôleur d’export du contrôle salarial

`ContractSalaryControlExportController` fournit aux futures interfaces un point d’entrée unique pour exporter un `ContractSalaryControlViewModel`. Il est indépendant de Flask, Django, FastAPI, Qt, wxPython et de toute CLI.

## Contrat d’appel

L’interface construit un `ContractSalaryControlExportRequest` avec :

- le `ContractSalaryControlViewModel` à exporter ;
- un `ContractSalaryControlExportFormat` (`CSV` ou `JSON`).

Le contrôleur retourne un `ContractSalaryControlExportResponse` contenant exactement :

- `content` ;
- `suggested_filename` ;
- `mime_type` ;
- `format`.

La requête, la réponse et le contrôleur sont des dataclasses immuables avec slots. Tous leurs paramètres sont validés strictement.

## Délégation

Le contrôleur ne connaît ni le CSV ni le JSON. Il délègue exclusivement à `ContractSalaryControlExporter`, puis recopie sans transformation les quatre valeurs produites par cette façade. Les exporteurs spécialisés restent les seuls responsables de la sérialisation, du nom de fichier et du type MIME.

```python
from application.control import (
    ContractSalaryControlExportController,
    ContractSalaryControlExportRequest,
)
from application.presentation import ContractSalaryControlExportFormat

response = ContractSalaryControlExportController().execute(
    ContractSalaryControlExportRequest(
        view_model=view_model,
        format=ContractSalaryControlExportFormat.CSV,
    )
)
```

L’écriture dans un fichier, la réponse HTTP ou l’ouverture d’une boîte de téléchargement reste à la charge de l’interface.
