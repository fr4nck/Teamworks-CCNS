# Régimes d'emploi canoniques

`EmploymentRegime` décrit la situation métier employée par le domaine CCNS.
Chaque situation n'est représentée que par un seul code afin que les règles et
les audits traitent toujours les profils équivalents de la même façon.

## Codes historiques conservés

Les codes suivants sont canoniques et restent les seuls membres de
`EmploymentRegime` pour les situations concernées :

| Situation métier | Code canonique | Code rencontré à l'import ou dans un type de contrat |
| --- | --- | --- |
| Apprentissage | `APPRENTICE` | `APPRENTICESHIP` |
| Service civique | `SERVICE_CIVIQUE` | `CIVIC_SERVICE` |
| Stage ou PFMP | `STAGE_PFMP` | `INTERNSHIP` |

La conversion des codes non canoniques est faite dans le mapping des contrats
historiques, avant la création de l'objet `Contract`. Ces codes ne doivent pas
être ajoutés comme membres supplémentaires de l'énumération.

## Stage et PFMP

Dans le périmètre actuel du moteur, un stage et une période de formation en
milieu professionnel (PFMP) ne portent aucune règle CCNS distincte. Ils sont
donc volontairement réunis sous le régime `STAGE_PFMP`. Une séparation future
ne sera justifiée que si une règle métier ou juridique différente doit être
appliquée et devra alors être documentée et couverte par un test dédié.
