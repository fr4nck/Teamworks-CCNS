# Provenance des fixtures TWD réelles — génération Git 2019

Ces six fixtures ne sont pas des fichiers synthétiques.

Elles réutilisent les blobs Git des modèles Teamword présents dans le dépôt au commit :

- commit : `405c10ba04c736095e4b9bb0a1aa2cf69faae058` ;
- auteur : Noethys ;
- date du commit : 27 avril 2019 ;
- message : `Déplacement des modèles de documents`.

Modèles :

- `Autorisation parentale mineurs - Exemple.twd` — blob Git `c209ce9da2d9fa2524822baf05c030be2754aa8c` ;
- `Certificat de travail - Exemple.twd` — `74df9a0606e73bf29222740458a1d35841c2839d` ;
- `Confirmation d'embauche - Exemple.twd` — `a7b2a8f04a5a609fb9dcf6bbf119f43d7c34ef75` ;
- `Contrat d'engagement éducatif - Exemple.twd` — `60e78d7fa30af84fbe5ad532a31abcd510e0efcc` ;
- `Contrat à durée déterminée - Exemple.twd` — `f2f78edf82ec48a46d6b43afb8d0ee5985a74472` ;
- `Lettre de refus - Exemple.twd` — `3294646df24fa9d37da1a031c5916e0c2747cbe0`.

Au SHA qualifié de départ de l'itération 3 (`2ae9fe2ddf79ccf45417bb86c98ad24352332381`), les six chemins courants pointent encore vers ces mêmes blobs. Les tests vérifient néanmoins explicitement l'égalité des octets et le diff structurel, afin que toute évolution future du corpus courant devienne visible.

La date ci-dessus est une date de commit Git, pas une date de modification de fichier issue de NTFS : Git ne conserve pas les mtimes des fichiers.

Les installations Windows mentionnées par l'utilisateur (`Program Files (x86)` et `Program Files`) ne sont pas accessibles à la CI. Aucune génération « 2022 » ou autre millésime n'est fabriquée à partir de ces chemins. Elle devra être ajoutée ici seulement à partir de vrais fichiers fournis et, si nécessaire, anonymisés.
