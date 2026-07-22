# Filtres et tris salariaux de l'audit CCNS

L'écran d'audit peut filtrer les lignes déjà chargées par statut salarial, source du minimum et présence d'un écart positif. Ces critères se combinent aux filtres historiques.

Les tris salariaux portent sur le statut, la rémunération contrôlée, le minimum applicable, la source et l'écart. Ils sont stables et placent toujours les valeurs absentes à la fin.

Les filtres, le tri, le résumé et l'export travaillent exclusivement sur les dictionnaires issus des `AuditRow` chargées. Ils ne relancent ni l'audit, ni le contrôleur salarial, ne font aucune requête SQL et conservent les montants en `Decimal`.

## Vérification manuelle

Dans l'écran wxPython, lancer l'audit puis vérifier chaque filtre et tri, leur remise à zéro, l'actualisation du résumé et l'ordre identique dans l'export CSV.
