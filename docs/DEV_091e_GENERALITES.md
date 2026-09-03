# 0.9.1e — Généralités

Critères de sortie de la corrective :

- les coordonnées restent visibles et pilotables directement depuis la page Généralités ;
- la saisie d'une ville de naissance étrangère est libre et ne dépend pas de `Villes.db3` ;
- le code postal de naissance est facultatif hors France ;
- la validation NIR attend le code département `99` pour une naissance à l'étranger ;
- les codes postaux étrangers ne doivent pas être convertis en entier ni forcés sur cinq chiffres ;
- la disposition doit pouvoir basculer entre une et deux colonnes selon la largeur réellement disponible et l'échelle d'interface ;
- les Snap Layouts Windows 11 et les forts niveaux de zoom ne doivent pas produire de champs ou boutons tronqués.

Le socle est fourni par `UTILS_Responsive.py` et `UTILS_Generalites_international.py`. `CTRL_Page_generalites_091e.py` isole les adaptations de la corrective sans recopier la logique métier historique de la fiche.