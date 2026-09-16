# Audit multi-version du patrimoine Teamword TWD

## Objet

Cette itération répond à la question : **les modèles Teamword issus des générations historiques réellement disponibles restent-ils automatiquement importables dans `DocumentModel v1`, et quelles évolutions réelles du format TWD faut-il supporter ?**

Le périmètre est volontairement borné aux sources effectivement disponibles. Aucun millésime n'est déduit à partir d'un chemin Windows ou d'un nom de fichier.

## Générations réellement disponibles

### Génération Git 2019

Les six modèles existaient au commit Git `405c10ba04c736095e4b9bb0a1aa2cf69faae058`, daté du 27 avril 2019 (`Déplacement des modèles de documents`). Les fixtures sous `tests/fixtures/twd/real/2019/` réutilisent **les blobs Git exacts** de ce commit.

### Génération dépôt qualifié 2026

Les six modèles courants sont lus dans `teamworks/Static/Documents/` au parent qualifié de l'itération 3 : `2ae9fe2ddf79ccf45417bb86c98ad24352332381`.

### Générations Windows externes

Le poste utilisateur possède également des copies sous :

- `C:\Program Files (x86)\Teamworks\static\Documents\` ;
- `C:\Program Files\Teamworks-CCNS\Static\Documents\`.

Ces fichiers ne sont pas accessibles dans la CI ni dans l'environnement de cette intervention. Ils sont donc **non testés** dans cette itération. Aucun corpus « 2022 » n'est inventé. Lorsqu'ils seront fournis, ils pourront être ajoutés comme fixtures réelles après vérification/anonymisation.

Git ne conserve pas les dates de modification NTFS. La date 2019 ci-dessus est la date du commit de provenance ; le SHA 2026 est un point de qualification Git, pas un mtime du fichier.

## Résultat majeur : stabilité byte-for-byte 2019 -> 2026

Pour les six modèles, le blob Git du commit 2019 et le blob du dépôt qualifié 2026 sont identiques. Les tests relisent néanmoins les deux chemins et comparent les octets ainsi que la représentation structurelle.

Conséquence : sur ce corpus Git, il n'y a **aucune évolution de format, structure, contenu, style, asset ou placeholder** entre les deux générations disponibles.

## Inventaire réel

Les métriques ci-dessous ont été calculées en CI avec `inspect_twd_bytes()` sur les 12 observations (6 modèles x 2 générations). Comme les deux générations sont identiques, une seule ligne par modèle suffit ; le SHA-256 et les compteurs valent à la fois pour 2019 et 2026.

| Modèle | SHA-256 source | Taille | Paragraphes | Text runs | Images | Symboles | Placeholders | Styles distincts |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Autorisation parentale mineurs | `8a9e83690279595ac16a67dfc27269a5ea548ef0dbf39fbeca7f660093ebc2d3` | 99 554 | 34 | 35 | 1 BMP | 0 | 2 | 5 |
| Certificat de travail | `a3cc5f8d5547eac7582e6778355993cce792f856699133348b435a861cee6f7e` | 98 710 | 33 | 34 | 1 BMP | 0 | 7 | 4 |
| Confirmation d'embauche | `792495e5f810ed2e95103dc77da115587ddc0bb9ff25bf4ab08b87df0825e614` | 99 770 | 41 | 41 | 1 BMP | 0 | 9 | 6 |
| Contrat d'engagement éducatif | `7b31181eba2f3887351bcbc668b24e581d86e0336741d94a727093f84c389ff7` | 102 869 | 73 | 79 | 1 BMP | 6 | 18 | 6 |
| Contrat à durée déterminée | `ac4686eedf5371cccfd54f84a2346a836123a54b59f9b1aa319578c2f34d7457` | 102 798 | 74 | 75 | 1 BMP | 0 | 18 | 6 |
| Lettre de refus | `5d4cae6ee1f9ce83b36225340a726de1064c0d88c7871a510e2043ebf890251b` | 99 214 | 33 | 34 | 1 BMP | 0 | 6 | 7 |

### Déclaration et format communs aux douze observations

- déclaration : `<?xml version="1.0" encoding="UTF-8"?>` ;
- namespace : `http://www.wxwidgets.org` ;
- `richtext version="1.0.0.0"` ;
- type d'image détecté : `image/bmp` ;
- liens : 0 ;
- tableaux : 0 ;
- sauts de page explicites : 0 ;
- structures inconnues : 0.

### Balises rencontrées

Tous les fichiers utilisent `richtext`, `paragraphlayout`, `paragraph`, `text`, `image` et `data`. Le contrat d'engagement éducatif utilise en plus `symbol`, six fois, avec le marqueur historique déjà qualifié par l'importeur.

### Attributs rencontrés

Le corpus expose, selon les modèles :

- `richtext.version` ;
- `paragraphlayout.textcolor`, `fontsize`, `fontstyle`, `fontweight`, `fontunderlined`, `fontface`, `alignment`, `parspacingafter`, `parspacingbefore`, `linespacing` ;
- `paragraph.alignment`, `leftindent`, `leftsubindent` ;
- `image.imagetype` ;
- `text.fontsize`, `fontstyle`, `fontweight`, `fontunderlined`, `fontface`.

Aucun nouvel attribut structurel n'apparaît entre 2019 et 2026.

### Styles, alignements, retraits, couleurs et polices

- alignements observés : `1`, `2`, `3` (gauche, centre, droite) ;
- retraits : `leftindent=100` / `leftsubindent=0` sur les contrats, `leftindent=1000` / `leftsubindent=0` sur des courriers ;
- couleur observée au niveau du layout : `#000000` ;
- polices : `MS Shell Dlg 2`, et `Tahoma` sur certains titres ;
- tailles : `8` et `16` points selon les modèles ;
- gras : `fontweight=92` ;
- italique : `fontstyle=93` dans la lettre de refus ;
- souligné : `fontunderlined=1` dans la lettre de refus.

Ces ensembles sont identiques entre les deux générations disponibles.

## Placeholders observés

| Modèle | Tokens observés |
|---|---|
| Autorisation parentale mineurs | `{PRENOM}`, `{NOM}` |
| Certificat de travail | `{CIVILITE}`, `{PRENOM}`, `{NOM}`, `{NUMSECU}`, `{CLASSIFICATION}`, `{DATEDEBUT}`, `{DATEFIN}` |
| Confirmation d'embauche | `{CIVILITE}`, `{NOM}`, `{PRENOM}`, `{ADRESSERESID}`, `{CPRESID}`, `{VILLERESID}`, `{CLASSIFICATION}`, `{DATEDEBUT}`, `{DATEFIN}` |
| Contrat d'engagement éducatif | `{CIVILITE}`, `{NOM}`, `{PRENOM}`, `{DATENAISS}`, `{CPNAISS}`, `{VILLENAISS}`, `{ADRESSERESID}`, `{CPRESID}`, `{VILLERESID}`, `{NUMSECU}`, `{CLASSIFICATION}`, `{DATEDEBUT}`, `{DATEFIN}`, `{ESSAI}`, `{NBREJOURS}`, `{REPARTITION}`, `{BRUTJOUR}`, `{VALEURPOINT}` |
| Contrat à durée déterminée | mêmes 18 tokens que le CEE |
| Lettre de refus | `{CIVILITE}`, `{NOM}`, `{PRENOM}`, `{ADRESSERESID}`, `{CPRESID}`, `{VILLERESID}` |

L'itération 3 qualifie cinq alias supplémentaires sur source métier vérifiée : `{CPNAISS}`, `{VILLENAISS}`, `{NUMSECU}`, `{ESSAI}`, `{VALEURPOINT}`. Restent volontairement non canoniques : `{NBREJOURS}`, `{REPARTITION}`, `{BRUTJOUR}`. Voir `DOCUMENT_FIELD_LEGACY_ALIASES.md`.

## Diff structurel

`TwdStructuralDiff` compare deux TWD en catégories distinctes :

```text
TwdStructuralDiff
- source_a
- source_b
- same_format
- structural_changes
- content_changes
- style_changes
- asset_changes
- placeholder_changes
- warnings
```

Il détecte aussi un cas « octets XML différents mais représentation normalisée identique » comme différence cosmétique, et expose `potentially_incompatible` lorsqu'une version/namespace ou une structure inconnue le justifie.

### Résultat 2019 -> 2026

| Modèle | Même format | Structure | Contenu | Styles | Assets | Placeholders | Conclusion |
|---|---|---|---|---|---|---|---|
| Autorisation parentale mineurs | oui | identique | identique | identiques | identique | identiques | stable |
| Certificat de travail | oui | identique | identique | identiques | identique | identiques | stable |
| Confirmation d'embauche | oui | identique | identique | identiques | identique | identiques | stable |
| Contrat d'engagement éducatif | oui | identique | identique | identiques | identique | identiques | stable |
| Contrat à durée déterminée | oui | identique | identique | identiques | identique | identiques | stable |
| Lettre de refus | oui | identique | identique | identiques | identique | identiques | stable |

Ici, « identique » est plus fort qu'une simple équivalence structurelle : les octets source sont également identiques.

## Import par génération

| Modèle | Génération | Import | Texte | Styles | Assets | Placeholders | Warnings patrimoniaux | Statut |
|---|---|---|---|---|---|---|---|---|
| Autorisation parentale mineurs | Git 2019 | succès | complet | complets | 1/1 | 2/2 canoniques | aucun | SUPPORTÉ |
| Autorisation parentale mineurs | dépôt 2026 | succès | complet | complets | 1/1 | 2/2 canoniques | aucun | SUPPORTÉ |
| Certificat de travail | Git 2019 | succès | complet | complets | 1/1 | 7/7 canoniques | aucun | SUPPORTÉ |
| Certificat de travail | dépôt 2026 | succès | complet | complets | 1/1 | 7/7 canoniques | aucun | SUPPORTÉ |
| Confirmation d'embauche | Git 2019 | succès | complet | complets | 1/1 | 9/9 canoniques | aucun | SUPPORTÉ |
| Confirmation d'embauche | dépôt 2026 | succès | complet | complets | 1/1 | 9/9 canoniques | aucun | SUPPORTÉ |
| Contrat d'engagement éducatif | Git 2019 | succès | complet | complets | 1/1 | 15/18 canoniques ; 3 conservés | variables legacy non canoniques | SUPPORTÉ AVEC PERTES MINEURES |
| Contrat d'engagement éducatif | dépôt 2026 | succès | complet | complets | 1/1 | 15/18 canoniques ; 3 conservés | variables legacy non canoniques | SUPPORTÉ AVEC PERTES MINEURES |
| Contrat à durée déterminée | Git 2019 | succès | complet | complets | 1/1 | 15/18 canoniques ; 3 conservés | variables legacy non canoniques | SUPPORTÉ AVEC PERTES MINEURES |
| Contrat à durée déterminée | dépôt 2026 | succès | complet | complets | 1/1 | 15/18 canoniques ; 3 conservés | variables legacy non canoniques | SUPPORTÉ AVEC PERTES MINEURES |
| Lettre de refus | Git 2019 | succès | complet | complets | 1/1 | 6/6 canoniques | aucun | SUPPORTÉ |
| Lettre de refus | dépôt 2026 | succès | complet | complets | 1/1 | 6/6 canoniques | aucun | SUPPORTÉ |

Les « pertes mineures » sont uniquement une absence de sémantisation canonique pour trois tokens ; leurs caractères restent présents dans le HTML importé. Aucun texte, style ou asset n'est supprimé dans le corpus testé.

## Matrice de compatibilité multi-version

| Modèle | Git 2019 | Dépôt qualifié 2026 | Diff structurel | Diff placeholders | Diff assets | Compatibilité |
|---|---|---|---|---|---|---|
| Autorisation parentale mineurs | testé | testé | aucune | aucune | aucune | SUPPORTÉ |
| Certificat de travail | testé | testé | aucune | aucune | aucune | SUPPORTÉ |
| Confirmation d'embauche | testé | testé | aucune | aucune | aucune | SUPPORTÉ |
| Contrat d'engagement éducatif | testé | testé | aucune | aucune | aucune | SUPPORTÉ AVEC PERTES MINEURES |
| Contrat à durée déterminée | testé | testé | aucune | aucune | aucune | SUPPORTÉ AVEC PERTES MINEURES |
| Lettre de refus | testé | testé | aucune | aucune | aucune | SUPPORTÉ |

Les générations des installations Windows externes sont **À INVESTIGUER** tant que leurs fichiers ne sont pas fournis. Cette matrice n'invente donc pas de colonne « 2022 ».

## Mesures de sortie

Deux dénominateurs sont distingués :

- **6 modèles uniques** ;
- **12 observations modèle-génération** réellement importées (6 en 2019 + 6 en 2026).

Résultats :

- import automatique : **12/12 = 100 %** des observations disponibles ;
- conservation texte/styles/assets : **12/12 = 100 %** sur le corpus testé ;
- fidélité complète stricte incluant la sémantisation de tous les placeholders : **8/12 = 66,7 %**, soit **4/6 modèles uniques** ;
- support avec pertes mineures : **4/12 observations**, les deux modèles de contrat dans les deux générations ;
- pertes majeures : **0/12** ;
- assets importés : **12/12 BMP** lors des imports, correspondant à 6 modèles dont les générations ont les mêmes octets ;
- structures inconnues réelles : **0** ;
- variantes historiques de structure détectées dans le dépôt : **0**.

## Réponse au critère principal

**Oui, toutes les générations historiques réellement disponibles dans l'historique Git étudié restent automatiquement importables dans `DocumentModel v1`.** Pour les six modèles, le format n'a pas évolué entre la génération Git 2019 et le dépôt qualifié 2026 : les sources sont byte-for-byte identiques.

Cette conclusion ne couvre pas encore les copies présentes dans les anciennes installations Windows du poste utilisateur. Il n'est donc pas possible d'affirmer que *tout* le patrimoine utilisateur, ni qu'une génération 2022 non fournie, est identique ou compatible.
