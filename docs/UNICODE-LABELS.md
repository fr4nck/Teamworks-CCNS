# Politique Unicode et UTF-8

Tous les fichiers source et toutes les ressources textuelles suivies par Git
sont enregistrés en UTF-8. Les libellés contiennent directement les caractères
Unicode corrects : aucune réparation au moment de l'affichage n'est nécessaire.

## Règles

- tous les fichiers texte et Python sont enregistrés en UTF-8 ;
- les nouveaux libellés doivent contenir directement les caractères Unicode corrects ;
- aucune correction locale ou centralisée de mojibake ne doit être ajoutée ;
- le contrôle `scripts/check_utf8.py` refuse les fichiers texte non UTF-8, les
  déclarations d'encodage source obsolètes et les séquences de mojibake connues ;
- les anciens encodages ne sont tolérés qu'à la lecture d'un fichier externe
  historique, dans une fonction explicitement située à cette frontière ;
- les nouvelles écritures et les exports texte utilisent UTF-8.

## Compatibilité historique

Les fichiers de langue historiques peuvent encore contenir des clés binaires
en ISO-8859-15 ou Windows-1252. `UTILS_Traduction` les décode uniquement lors
de leur chargement. Cette tolérance ne s'applique ni aux sources ni aux
ressources versionnées.

Les mois et leurs formes abrégées sont stockés directement sous les formes
`Février`, `Août`, `Décembre`, `Fév.` et `Déc.`.
