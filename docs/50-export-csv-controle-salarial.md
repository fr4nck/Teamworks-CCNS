# Export CSV du contrôle salarial

`ContractSalaryControlCsvExporter` transforme exclusivement un `ContractSalaryControlViewModel` déjà produit par le présentateur. Il ne consulte aucun repository et ne relance aucun calcul salarial.

## Format

- encodage logique UTF-8 ;
- séparateur point-virgule ;
- fins de ligne CRLF déterministes ;
- une ligne d’en-tête puis une ligne par résultat, dans l’ordre exact du view model ;
- valeurs brutes pour les dates, UUID, énumérations et montants ;
- valeur absente représentée par `__ABSENT__` ;
- échappement standard CSV des séparateurs, guillemets et retours à la ligne.

## Résultat

L’exporteur retourne un `ContractSalaryControlCsvExport` immuable contenant :

- `content` : le texte CSV ;
- `suggested_filename` : `controle-salarial-AAAA-MM-JJ.csv`, calculé uniquement depuis la date de référence ;
- `mime_type` : `text/csv; charset=utf-8`.

L’écriture du fichier, son téléchargement ou son stockage restent sous la responsabilité de l’interface appelante.
