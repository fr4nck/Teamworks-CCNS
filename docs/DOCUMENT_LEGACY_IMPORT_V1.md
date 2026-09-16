# Import legacy Teamword TWD vers DocumentModel v1

## Périmètre

Le lecteur v1 importe des fichiers Teamword TWD sérialisés au format XML wxWidgets RichText vers `DocumentModel v1`. Il se trouve dans `infrastructure/documents/twd_importer.py` et ne fait pas partie de `domain.documents`.

Il ne remplace ni Teamword wx, ni le publiposteur historique, ni un futur éditeur Qt de production.

## Contrat d'import

L'entrée est une séquence d'octets ou un chemin de fichier. La sortie `LegacyImportResult` contient :

- `document` ;
- `source` ;
- `source_hash` (SHA-256) ;
- `warnings` ;
- `unsupported_features` ;
- `imported_assets` ;
- `placeholders_recognized` ;
- `placeholders_unknown`.

L'import est strictement non destructif : le fichier TWD source n'est jamais sauvegardé ni normalisé en place.

## Format qualifié

Le corpus réel disponible dans le dépôt, pour les générations Git 2019 et dépôt qualifié 2026, utilise :

- XML UTF-8 ;
- racine `richtext` ;
- namespace `http://www.wxwidgets.org` ;
- version richtext `1.0.0.0` ;
- `paragraphlayout`, `paragraph`, `text`, `image`, `data` et, sur un modèle, `symbol` ;
- images BMP embarquées sous forme hexadécimale.

Les générations externes présentes dans les installations Windows ne sont pas utilisées en CI et ne sont pas considérées testées tant que leurs fichiers ne sont pas fournis ou versionnés comme fixtures réelles.

## Comparaison structurelle

`infrastructure.documents.twd_compare` complète l'importeur avec :

- `TwdInventory` : inventaire normalisé d'un TWD ;
- `TwdStructuralDiff` : diff sémantique entre deux fichiers ;
- `inspect_twd_bytes()` ;
- `compare_twd_bytes()`.

Le comparateur distingue structure, contenu, styles, assets et placeholders. Un simple changement d'indentation XML peut ainsi être classé comme cosmétique au lieu d'être confondu avec une évolution de format.

## Structures inconnues et versions inattendues

L'importeur et l'inspecteur adoptent un comportement conservateur :

- XML invalide : erreur explicite ;
- DTD/entités : refus ;
- namespace inattendu : refus de l'importeur ;
- version richtext non qualifiée : warning et `unsupported_features` côté importeur ;
- élément/attribut inconnu : signalement ; le texte est conservé autant que possible par l'importeur ;
- placeholder non reconnu : conservé visiblement, jamais remplacé silencieusement.

## Fixtures

### Fixtures réelles

`tests/fixtures/twd/real/2019/` contient uniquement des blobs historiques réellement présents dans l'historique Git du dépôt. Leur provenance est documentée dans `PROVENANCE.md`.

### Fixtures techniques

`tests/fixtures/twd/TECHNIQUE_url_pagebreak.twd` et les XML construits dans les tests couvrent les cas techniques absents du corpus réel : URL, pagebreak, structure/attribut inconnu, XML invalide et version inattendue.

Une fixture technique n'est jamais utilisée comme preuve d'une génération Teamworks historique.

## Portabilité

`domain.documents` doit rester importable sans :

- `wx` / `wx.richtext` ;
- `PySide6`, `PyQt5`, `PyQt6` ;
- `GestionDB` ;
- UI Teamworks.

Le parsing wxRichText XML est une responsabilité infrastructure/legacy. Le core reçoit seulement des objets et données neutres.
