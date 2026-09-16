# Audit du format Teamword historique TWD — itération 2

## Objet

Cette note qualifie le format réellement présent dans `teamworks/Static/Documents/` au commit `a87b9da4e9cb7f8575c7835c0c4ee0e6dc568527` et fixe le périmètre du `LegacyImporter` de l'itération 2.

Une première recherche fondée seulement sur la recherche de code GitHub avait conclu à tort que les `.twd` n'étaient pas présents. L'inspection directe de l'API contents et des blobs Git confirme au contraire la présence des six modèles suivis dans le dépôt. La recherche de code n'est donc pas utilisée comme preuve d'absence pour ce corpus.

## Corpus réel du dépôt

| Modèle réel | Blob Git | Taille |
| --- | --- | ---: |
| `Autorisation parentale mineurs - Exemple.twd` | `c209ce9da2d9fa2524822baf05c030be2754aa8c` | 99 554 octets |
| `Certificat de travail - Exemple.twd` | `74df9a0606e73bf29222740458a1d35841c2839d` | 98 710 octets |
| `Confirmation d'embauche - Exemple.twd` | `a7b2a8f04a5a609fb9dcf6bbf119f43d7c34ef75` | 99 770 octets |
| `Contrat d'engagement éducatif - Exemple.twd` | `60e78d7fa30af84fbe5ad532a31abcd510e0efcc` | 102 869 octets |
| `Contrat à durée déterminée - Exemple.twd` | `f2f78edf82ec48a46d6b43afb8d0ee5985a74472` | 102 798 octets |
| `Lettre de refus - Exemple.twd` | `3294646df24fa9d37da1a031c5916e0c2747cbe0` | 99 214 octets |

Ces six fichiers sont le **CORPUS RÉEL** de l'itération 2.

## Format réellement observé

Les six `.twd` sont des fichiers **XML UTF-8 wxWidgets RichText** directement lisibles. Ils ne sont ni des archives, ni un conteneur binaire, ni du RTF déguisé.

En-tête commun observé :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<richtext version="1.0.0.0" xmlns="http://www.wxwidgets.org">
  <paragraphlayout
      textcolor="#000000"
      fontsize="8"
      fontstyle="90"
      fontweight="90"
      fontunderlined="0"
      fontface="MS Shell Dlg 2"
      alignment="1"
      parspacingafter="10"
      parspacingbefore="0"
      linespacing="10">
```

Le namespace, la version de racine et la structure correspondent au sérialiseur `wxRichTextXMLHandler` de wxWidgets.

### Balises principales observées

Sur le corpus réel :

- `richtext` : racine ;
- `paragraphlayout` : style/layout par défaut du document ;
- `paragraph` : paragraphes ;
- `text` : fragments de texte avec surcharge de style éventuelle ;
- `image` : image embarquée ;
- `data` : contenu hexadécimal de l'image ;
- `symbol` : observé dans `Contrat d'engagement éducatif - Exemple.twd`.

Aucune balise de tableau n'a été observée dans les six fichiers.

### Paragraphes et alignements

Les documents sont organisés en paragraphes successifs. Les valeurs d'alignement observées sont :

- `alignment="1"` : gauche ;
- `alignment="2"` : centré ;
- `alignment="3"` : droite.

Les signatures et mentions de fin utilisent notamment l'alignement à droite. Les titres utilisent fréquemment le centrage.

### Retraits et espacements

Attributs observés :

- `leftindent` ;
- `leftsubindent` ;
- `parspacingbefore` ;
- `parspacingafter` ;
- `linespacing`.

wxRichText exprime retraits et espacements de paragraphe en dixièmes de millimètre. L'importeur convertit donc, par exemple, `leftindent="1000"` en `margin-left: 100mm` et `parspacingafter="10"` en `margin-bottom: 1mm`.

### Styles de caractères

Attributs observés :

- `textcolor` ;
- `fontsize` ;
- `fontface` ;
- `fontweight` ;
- `fontstyle` ;
- `fontunderlined`.

Valeurs historiques effectivement rencontrées :

- `fontweight="90"` : normal ;
- `fontweight="92"` : gras ;
- `fontstyle="90"` : normal ;
- `fontstyle="93"` : italique ;
- `fontunderlined="1"` : souligné.

`Lettre de refus - Exemple.twd` combine notamment italique et souligné sur `Objet :`. Les titres de plusieurs modèles sont en taille 16, Tahoma, gras.

### Images

Chaque modèle réel contient au début du document une image embarquée :

```xml
<image imagetype="1">
  <data>424D...</data>
</image>
```

Le contenu de `<data>` est du **binaire encodé en hexadécimal**, et non du base64. Le préfixe `424D` correspond à la signature `BM` d'un bitmap Windows BMP.

Le lecteur extrait les octets sans passer par wxPython et les transforme en `Asset` du `DocumentModel`. L'URI HTML devient `asset://<uuid>`.

Les identifiants de document et d'asset sont déterministes à partir du SHA-256 de la source et de l'asset, afin que deux imports du même TWD produisent la même identité technique.

### Symboles et sauts de ligne internes

`Contrat d'engagement éducatif - Exemple.twd` contient plusieurs :

```xml
<symbol>29</symbol>
```

Le code d'exemple wxWidgets RichText utilise explicitement le caractère 29 comme saut de ligne interne à un paragraphe. L'importeur convertit donc le symbole 29 en `<br>` et enregistre le nombre de conversions dans la provenance du document. Cette conversion n'est pas classée comme perte.

Les autres valeurs éventuelles de `<symbol>` sont conservées sous une forme visible et signalées comme non supportées, plutôt que supprimées silencieusement.

### Liens

Aucun attribut `url` n'a été observé dans les six modèles réels.

Le format wxRichText sait toutefois sérialiser une URL dans l'attribut `url` d'un objet texte. Une **FIXTURE TECHNIQUE**, distincte du corpus réel, vérifie uniquement cette capacité du lecteur :

`tests/fixtures/twd/TECHNIQUE_url_pagebreak.twd`.

Cette fixture ne sert pas à augmenter artificiellement le taux de compatibilité du patrimoine réel.

### Tableaux

Aucun tableau n'a été observé dans les six TWD du dépôt. Aucun support de tableau TWD n'est donc déclaré sur la base de ce corpus. Le sujet reste `À INVESTIGUER` avec un vrai modèle contenant un tableau.

### Listes

Aucune structure de liste wxRichText dédiée n'a été observée dans le corpus. Les contrats contiennent en revanche le marqueur historique `<symbol>29</symbol>`, interprété comme saut de ligne interne conformément au comportement wxRichText documenté ci-dessus.

### Pagination

Aucun `pagebreak` n'a été observé dans les six fichiers réels.

Le sérialiseur wxRichText supporte cependant l'attribut `pagebreak`. La fixture technique `TECHNIQUE_url_pagebreak.twd` vérifie sa conversion vers :

```css
page-break-before: always
```

La pagination réelle des six modèles reste donc simple : aucun saut de page explicite à préserver n'a été constaté.

### Métadonnées

Aucun bloc de métadonnées Teamword spécifique n'a été observé dans le corpus. Les métadonnées structurelles disponibles sont principalement :

- déclaration XML UTF-8 ;
- namespace wxWidgets ;
- version `richtext="1.0.0.0"` ;
- attributs du `paragraphlayout`.

Le `DocumentModel` importé ajoute de la provenance technique sans modifier la source :

- `legacy_format = wx-richtext-xml` ;
- `legacy_namespace` ;
- `legacy_version` ;
- `legacy_source` ;
- `legacy_source_sha256` ;
- compteur `legacy_symbol_29_line_breaks` lorsqu'il existe.

## Placeholders réellement observés

Les placeholders restent du texte `{TOKEN}` dans les éléments `<text>`. L'importeur les classe avec le registre canonique de l'itération 1.

### Déjà reconnus par le registre v1

- `{NOM}` ;
- `{PRENOM}` ;
- `{CIVILITE}` ;
- `{DATENAISS}` ;
- `{ADRESSERESID}` ;
- `{CPRESID}` ;
- `{VILLERESID}` ;
- `{CLASSIFICATION}` ;
- `{DATEDEBUT}` ;
- `{DATEFIN}`.

Ils sont convertis en champs sémantiques `data-pmsl-field` par `upgrade_legacy_placeholders()`.

### Observés mais non mappés dans le registre v1

- `{NUMSECU}` ;
- `{CPNAISS}` ;
- `{VILLENAISS}` ;
- `{ESSAI}` ;
- `{NBREJOURS}` ;
- `{REPARTITION}` ;
- `{BRUTJOUR}` ;
- `{VALEURPOINT}`.

L'itération 2 **ne crée pas de nouveaux champs métier canoniques par supposition**. Ces tokens sont conservés littéralement dans le document importé, retournés dans `placeholders_unknown` et signalés dans `warnings`. Leur arbitrage sémantique appartient à une évolution du registre métier, pas au parseur TWD.

## Classification du corpus réel

Les six fichiers couvrent plusieurs caractéristiques simultanément. Ils ne sont pas forcés artificiellement dans une nomenclature A→G exclusive.

| Modèle | Caractéristiques réellement couvertes |
| --- | --- |
| Autorisation parentale | texte, paragraphes, centrage/droite, titre stylé, BMP embarqué, placeholders simples |
| Certificat de travail | texte, paragraphes, alignements, BMP, variables contrat/salarié, token `{NUMSECU}` non mappé |
| Confirmation d'embauche | texte long, retraits, gras, alignements, BMP, adresse + variables contrat |
| Contrat d'engagement éducatif | document long, titres gras, retraits, BMP, nombreuses variables, `<symbol>29</symbol>` |
| Contrat à durée déterminée | document long, titres gras, retraits, BMP, nombreuses variables |
| Lettre de refus | texte, retrait 1000, italique, souligné, alignements, BMP, variables adresse |

### FIXTURE TECHNIQUE complémentaire

`TECHNIQUE_url_pagebreak.twd` couvre uniquement deux mécanismes wxRichText absents des six vrais modèles : URL et saut de page explicite.

Elle est exclue du calcul de proportion de patrimoine repris.

## Legacy importer

Le lecteur est placé dans :

`infrastructure/documents/twd_importer.py`

Il utilise `xml.etree.ElementTree` et ne dépend pas de wxPython. `domain.documents` reste indépendant de wx, Qt et de la base de données.

La lecture est non destructive : aucun fichier `.twd` source n'est écrit ou normalisé.

Contrat de résultat :

```text
LegacyImportResult
- document
- source
- source_hash
- warnings
- unsupported_features
- imported_assets
- placeholders_recognized
- placeholders_unknown
```

Le lecteur préfère une perte visible et tracée à une suppression silencieuse :

- élément XML inconnu : texte enfant conservé si possible + `unsupported_features` ;
- attribut inconnu : signalement ;
- placeholder non mappé : texte conservé ;
- image non reconnue par signature : octets conservés comme asset générique + signalement ;
- version wxRichText autre que `1.0.0.0` : import tentatif + avertissement.

Les DTD et entités XML personnalisées sont refusées.

## Matrice de fidélité du corpus réel

La colonne `Variables` distingue volontairement la conservation textuelle de la reconnaissance métier. Un token non mappé n'est pas perdu, mais il ne devient pas encore un champ sémantique canonique.

| Modèle | Texte | Styles | Images | Liens | Tableaux | Variables | Pagination | Statut |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Autorisation parentale | SUPPORTÉ | SUPPORTÉ | SUPPORTÉ | N/A | N/A | SUPPORTÉ | N/A | SUPPORTÉ |
| Certificat de travail | SUPPORTÉ | SUPPORTÉ | SUPPORTÉ | N/A | N/A | PARTIEL — `{NUMSECU}` conservé mais non mappé | N/A | SUPPORTÉ AVEC PERTES MINEURES |
| Confirmation d'embauche | SUPPORTÉ | SUPPORTÉ | SUPPORTÉ | N/A | N/A | SUPPORTÉ | N/A | SUPPORTÉ |
| Contrat d'engagement éducatif | SUPPORTÉ | SUPPORTÉ | SUPPORTÉ | N/A | N/A | PARTIEL — 8 tokens conservés mais non mappés | N/A | SUPPORTÉ AVEC PERTES MINEURES |
| Contrat à durée déterminée | SUPPORTÉ | SUPPORTÉ | SUPPORTÉ | N/A | N/A | PARTIEL — 8 tokens conservés mais non mappés | N/A | SUPPORTÉ AVEC PERTES MINEURES |
| Lettre de refus | SUPPORTÉ | SUPPORTÉ | SUPPORTÉ | N/A | N/A | SUPPORTÉ | N/A | SUPPORTÉ |

`N/A` signifie que la fonction n'est pas présente dans ce modèle réel et n'est donc pas utilisée pour juger sa fidélité.

## Critère de reprise automatique

Pour cette itération, **un modèle est automatiquement repris** si :

1. son `.twd` réel est lu sans intervention manuelle ;
2. un `DocumentModel v1` valide est produit ;
3. le texte et les assets observés sont conservés ;
4. les variables connues sont sémantisées ;
5. les variables inconnues sont conservées et explicitement signalées ;
6. le fichier source reste octet pour octet intact.

La suite `tests/test_twd_legacy_importer.py` exécute ce critère sur les six fichiers réels. Lorsque les six tests réels sont verts, la proportion qualifiée est :

**6 / 6 = 100 % des modèles Teamword présents dans ce corpus dépôt importables automatiquement dans `DocumentModel v1`.**

Ce chiffre **ne signifie pas 100 % de fidélité sémantique**, et il ne doit pas être extrapolé au patrimoine utilisateur hors dépôt. Sur les six modèles, trois ont tous leurs placeholders observés déjà mappés par le registre v1 et trois conservent au moins un token non mappé.

## Corpus historique multi-version hors CI

Le poste utilisateur possède également les mêmes six modèles dans :

- ancienne installation : `C:\Program Files (x86)\Teamworks\static\Documents\` ;
- installation actuelle : `C:\Program Files\Teamworks-CCNS\Static\Documents\`.

Ces chemins locaux ne sont **jamais** requis par les tests CI.

Ils constituent un corpus historique multi-version potentiel. Une comparaison de format pourra être ajoutée lorsque les anciennes versions seront fournies ou intégrées comme fixtures anonymisées. Le protocole de comparaison devra au minimum relever :

- hash source ;
- namespace/version wxRichText ;
- ensemble de balises et attributs ;
- nombre/type/hash des assets ;
- placeholders ;
- différences structurelles de paragraphes et styles.

À ce stade, aucune conclusion n'est formulée sur une évolution du format entre l'ancienne installation Teamworks et Teamworks-CCNS faute d'octets de l'ancienne installation dans le dépôt.

## Limites restantes

- tableaux TWD : aucun exemple réel dans le corpus, donc `À INVESTIGUER` ;
- `leftsubindent` non nul : non observé ; l'importeur le signale comme perte potentielle au lieu de simuler une équivalence CSS incertaine ;
- versions wxRichText différentes de `1.0.0.0` : import tentatif signalé comme non qualifié ;
- formats d'image sans signature BMP/PNG/JPEG/GIF : octets conservés comme asset générique et signalés ;
- huit placeholders métier réels restent à arbitrer dans le registre canonique.

## Références techniques utilisées pour interpréter le format

- `wxWidgets/src/richtext/richtextxml.cpp` : racine `richtext`, version/namespace, sérialisation des attributs, `url`, `pagebreak`, `imagetype` ;
- `wxWidgets/samples/richtext/richtext.cpp` : usage du caractère 29 comme saut de ligne interne ;
- documentation `wx.TextAttr` : retraits, espacements et tabulations exprimés en dixièmes de millimètre, tailles de police en points.
