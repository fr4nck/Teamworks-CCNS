# Audit du format legacy Teamword TWD/XML

## Objet et correction de l'audit initial

L'itération 2 qualifie la reprise des modèles Teamword historiques vers `DocumentModel v1` à partir du **corpus réellement versionné dans le dépôt**.

Un premier arrêt avait conclu à tort à l'absence de fichiers `.twd` après une recherche de code GitHub. Cette conclusion provenait d'une méthode de recherche incomplète. L'inspection directe de l'arbre Git, de l'API `contents` et des blobs au commit parent `a87b9da4e9cb7f8575c7835c0c4ee0e6dc568527` confirme les fichiers sous :

`teamworks/Static/Documents/`

La recherche de code seule ne doit donc pas être utilisée comme preuve d'absence d'un fichier binaire, historique ou peu indexé.

## Corpus réel qualifié

Les six fichiers ci-dessous constituent le corpus réel de cette itération. Ils sont lus en place et ne sont jamais réécrits par les tests ni par l'importeur.

| Modèle réel | Blob Git au parent | Taille | Catégories principales |
|---|---|---:|---|
| `Autorisation parentale mineurs - Exemple.twd` | `c209ce9da2d9fa2524822baf05c030be2754aa8c` | 99 554 o | texte, titre, alignements, image, variables |
| `Certificat de travail - Exemple.twd` | `74df9a0606e73bf29222740458a1d35841c2839d` | 98 710 o | texte, titre, image, variables, bloc signature |
| `Confirmation d'embauche - Exemple.twd` | `a7b2a8f04a5a609fb9dcf6bbf119f43d7c34ef75` | 99 770 o | texte, retraits, gras, image, variables |
| `Contrat d'engagement éducatif - Exemple.twd` | `60e78d7fa30af84fbe5ad532a31abcd510e0efcc` | 102 869 o | document long, styles, image, variables, `symbol=29` |
| `Contrat à durée déterminée - Exemple.twd` | `f2f78edf82ec48a46d6b43afb8d0ee5985a74472` | 102 798 o | document long, styles, image, variables |
| `Lettre de refus - Exemple.twd` | `3294646df24fa9d37da1a031c5916e0c2747cbe0` | 99 214 o | retraits, italique, souligné, image, variables |

Les tailles et SHAs ci-dessus sont ceux des entrées Git du corpus au commit parent. Le `LegacyImportResult.source_hash` est, lui, un SHA-256 calculé sur les octets source au moment de l'import.

## Format réel observé

Les six fichiers sont des **documents XML UTF-8 wxWidgets RichText**, pas des archives ZIP, pas des conteneurs OLE et pas du RTF renommé.

Racine observée sur les six fichiers :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<richtext version="1.0.0.0" xmlns="http://www.wxwidgets.org">
  <paragraphlayout ...>
    ...
  </paragraphlayout>
</richtext>
```

Cette structure correspond au format sérialisé par `wxRichTextXMLHandler`. Le lecteur de l'itération 2 n'a donc besoin ni de `wx` ni de `wx.richtext` : il s'appuie sur `xml.etree.ElementTree` et reste dans `infrastructure/documents/`.

### Balises réellement observées

- `richtext` : racine, version `1.0.0.0`, namespace wxWidgets ;
- `paragraphlayout` : style par défaut du document ;
- `paragraph` : paragraphes et attributs de paragraphe ;
- `text` : segments de texte, avec attributs de caractère éventuels ;
- `image` + `data` : image embarquée ;
- `symbol` : observé avec la valeur `29` dans le contrat d'engagement éducatif.

Aucune balise de tableau, aucun lien et aucun saut de page n'a été observé dans les six fichiers réels inspectés.

### Styles réellement observés

Attributs de document/paragraphe/caractère rencontrés :

- `textcolor` ;
- `fontsize` ;
- `fontstyle` ;
- `fontweight` ;
- `fontunderlined` ;
- `fontface` ;
- `alignment` ;
- `parspacingafter` ;
- `parspacingbefore` ;
- `linespacing` ;
- `leftindent` ;
- `leftsubindent`.

Valeurs significatives observées :

- `alignment="1"` : gauche ;
- `alignment="2"` : centré ;
- `alignment="3"` : droite ;
- `fontweight="90"` : normal ;
- `fontweight="92"` : gras ;
- `fontstyle="90"` : normal ;
- `fontstyle="93"` : italique ;
- `fontunderlined="1"` : souligné ;
- `fontsize="16"` sur plusieurs titres ;
- `leftindent="100"` et `leftindent="1000"` selon les blocs.

Les retraits et espacements wx sont exprimés en dixièmes de millimètre. L'importeur les projette en CSS `mm`. Les tailles de police sont projetées en points. `DocumentModel` reste indépendant de ces conventions wx : elles sont traduites par l'adaptateur legacy.

### Images

Chaque modèle réel contient une image embarquée au début du document :

```xml
<image imagetype="1">
  <data>424D...</data>
</image>
```

`424D` est la signature binaire `BM` d'un bitmap Windows. Les octets sont encodés en **hexadécimal** dans le XML, et non en base64.

L'importeur :

1. décode la chaîne hexadécimale ;
2. identifie le format par signature binaire plutôt que par la seule valeur `imagetype` ;
3. crée un `Asset` `image/bmp` ;
4. calcule son SHA-256 ;
5. génère un UUID déterministe à partir du hash source, de l'index et du hash de l'asset ;
6. remplace l'image dans le HTML par une URI `asset://<uuid>`.

Les octets de l'image sont donc récupérés sans dépendance wx.

### `symbol=29`

Le contrat d'engagement éducatif contient plusieurs :

```xml
<symbol>29</symbol>
```

Le code de démonstration wxRichText utilise explicitement le caractère 29 comme marqueur de saut de ligne à l'intérieur d'un paragraphe. L'importeur le convertit en `<br>` et conserve le nombre converti dans `metadata.attributes.legacy_symbol_29_line_breaks`.

Il ne s'agit donc pas, pour ce corpus, d'une puce arbitraire à deviner.

### Liens, tableaux et pagination

- **Liens** : absents des six modèles réels. Le format wxRichText sérialise un lien via l'attribut `url` d'un segment ; ce cas est vérifié par une fixture technique artificielle.
- **Saut de page** : absent des six modèles réels. L'attribut wxRichText `pagebreak` est vérifié par la même fixture technique et projeté en `page-break-before: always`.
- **Tableaux** : absents des six modèles réels. Aucune structure de tableau n'est inventée pour cette itération ; la reprise de tableaux TWD reste `À INVESTIGUER` lorsqu'un vrai exemple sera disponible.

## Variables historiques observées

L'importeur recense d'abord les tokens historiques puis applique le registre sémantique de `domain.documents`.

### Variables déjà reconnues par le registre v1

- `{NOM}` -> `SALARIE_NOM`
- `{PRENOM}` -> `SALARIE_PRENOM`
- `{CIVILITE}` -> `SALARIE_CIVILITE`
- `{DATENAISS}` -> `SALARIE_DATE_NAISSANCE`
- `{ADRESSERESID}` -> `SALARIE_ADRESSE`
- `{CPRESID}` -> `SALARIE_CODE_POSTAL`
- `{VILLERESID}` -> `SALARIE_VILLE`
- `{CLASSIFICATION}` -> `CONTRAT_CLASSIFICATION`
- `{DATEDEBUT}` -> `CONTRAT_DATE_DEBUT`
- `{DATEFIN}` -> `CONTRAT_DATE_FIN`

### Variables observées mais non encore mappées sémantiquement

- `{NUMSECU}`
- `{CPNAISS}`
- `{VILLENAISS}`
- `{ESSAI}`
- `{NBREJOURS}`
- `{REPARTITION}`
- `{BRUTJOUR}`
- `{VALEURPOINT}`

Ces tokens **ne sont pas supprimés et ne sont pas renommés arbitrairement**. Ils restent visibles dans le HTML importé et sont retournés dans `LegacyImportResult.placeholders_unknown`. Leur ajout au registre canonique doit être une décision de vocabulaire/domaine séparée, avec source de vérité explicitée.

## Corpus réel et fixture technique

### Corpus réel

Les six `.twd` suivis dans `teamworks/Static/Documents/` sont la seule base du pourcentage de reprise automatique.

Ils couvrent ensemble :

- texte simple et documents longs ;
- gras, italique, souligné, taille et police ;
- alignements gauche/centre/droite ;
- retraits ;
- image embarquée ;
- variables de fusion ;
- sauts de ligne internes `symbol=29` ;
- documents simples et complexes.

### Fixture technique artificielle

`tests/fixtures/twd/TECHNIQUE_url_pagebreak.twd` est explicitement artificielle. Elle sert uniquement à verrouiller deux capacités du format wxRichText absentes du corpus réel :

- `text url="https://..."` ;
- `paragraph pagebreak="1"`.

Elle est **exclue** du calcul de couverture patrimoniale. Aucun faux modèle de tableau n'est créé.

## LegacyImportResult et non-destruction

L'importeur expose :

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

Principes :

- lecture seule du `.twd` ;
- SHA-256 calculé avant conversion ;
- aucun réenregistrement TWD ;
- IDs document/asset déterministes pour un même contenu source ;
- contenu inconnu signalé au lieu d'être silencieusement prétendu supporté ;
- texte d'un élément XML inconnu conservé autant que possible ;
- aucune dépendance `wx`, `PySide6` ou `PyQt` dans l'importeur ou `domain.documents`.

## Matrice de fidélité du corpus réel

`À INVESTIGUER — absent du modèle réel` indique que le fichier ne permet pas de mesurer cette fonction. `SUPPORTÉ — aucun saut explicite` signifie que le flux observé est conservé ; le mécanisme wxRichText `pagebreak` est couvert séparément par la fixture technique.

| Modèle | Texte | Styles | Images | Liens | Tableaux | Variables | Pagination | Statut |
|---|---|---|---|---|---|---|---|---|
| Autorisation parentale mineurs | SUPPORTÉ | SUPPORTÉ | SUPPORTÉ (1 BMP) | À INVESTIGUER — absent du modèle réel | À INVESTIGUER — absent du modèle réel | SUPPORTÉ (2/2) | SUPPORTÉ — aucun saut explicite | **SUPPORTÉ** |
| Certificat de travail | SUPPORTÉ | SUPPORTÉ | SUPPORTÉ (1 BMP) | À INVESTIGUER — absent du modèle réel | À INVESTIGUER — absent du modèle réel | PARTIEL — 6/7 sémantiques, `{NUMSECU}` conservé | SUPPORTÉ — aucun saut explicite | **SUPPORTÉ AVEC PERTES MINEURES** |
| Confirmation d'embauche | SUPPORTÉ | SUPPORTÉ | SUPPORTÉ (1 BMP) | À INVESTIGUER — absent du modèle réel | À INVESTIGUER — absent du modèle réel | SUPPORTÉ (9/9) | SUPPORTÉ — aucun saut explicite | **SUPPORTÉ** |
| Contrat d'engagement éducatif | SUPPORTÉ | SUPPORTÉ — `symbol=29` -> `<br>` | SUPPORTÉ (1 BMP) | À INVESTIGUER — absent du modèle réel | À INVESTIGUER — absent du modèle réel | PARTIEL — 10/18 sémantiques, 8 conservées | SUPPORTÉ — aucun saut explicite | **SUPPORTÉ AVEC PERTES MINEURES** |
| Contrat à durée déterminée | SUPPORTÉ | SUPPORTÉ | SUPPORTÉ (1 BMP) | À INVESTIGUER — absent du modèle réel | À INVESTIGUER — absent du modèle réel | PARTIEL — 10/18 sémantiques, 8 conservées | SUPPORTÉ — aucun saut explicite | **SUPPORTÉ AVEC PERTES MINEURES** |
| Lettre de refus | SUPPORTÉ | SUPPORTÉ — italique + souligné inclus | SUPPORTÉ (1 BMP) | À INVESTIGUER — absent du modèle réel | À INVESTIGUER — absent du modèle réel | SUPPORTÉ (6/6) | SUPPORTÉ — aucun saut explicite | **SUPPORTÉ** |

La perte mineure indiquée ici concerne **la sémantisation automatique de certains tokens métier**, pas la suppression de leur texte : les placeholders inconnus restent présents tels quels dans le `DocumentModel`.

## Mesure de reprise automatique

Le dénominateur est strictement le corpus réel suivi dans le dépôt : **6 modèles**.

Critère d'« import automatique réussi » :

1. le fichier réel est lu sans modification ;
2. un `DocumentModel v1` valide est produit ;
3. le texte attendu est présent ;
4. l'image embarquée est décodée et rattachée comme `Asset` ;
5. les placeholders connus sont sémantisés ;
6. les placeholders inconnus sont conservés et signalés ;
7. toute fonction structurelle non prise en charge est exposée dans `unsupported_features`.

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
