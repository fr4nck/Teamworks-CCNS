# Libellés Unicode historiques

Teamworks contient encore des modules anciens enregistrés avec plusieurs encodages. La couche `UTILS_Traduction` normalise désormais les séquences de mojibake récupérables et applique des corrections explicites aux libellés dont le caractère original a été remplacé par `�`.

## Règles

- les nouveaux fichiers texte et Python sont enregistrés en UTF-8 ;
- les nouveaux libellés doivent contenir directement les caractères Unicode corrects ;
- aucune nouvelle correction locale de type `replace()` ne doit être ajoutée dans les écrans ;
- les cas historiques doivent être centralisés dans `UTILS_Traduction.CorrigeMojibake` et couverts par un test ;
- une chaîne ambiguë contenant `�` ne doit pas être corrigée par supposition.

## Cas corrigés

Les mois complets et abrégés utilisés dans les calendriers sont couverts, notamment `Février`, `Août`, `Décembre`, `Fév.` et `Déc.`.
