# Format documentaire PMSL / Teamworks — version 1

Statut : **expérimental**, format portable du moteur documentaire ; il ne remplace pas les modèles wx/TWD de production et ne constitue pas un choix d'éditeur Qt de production.

## But

Le format v1 décrit un document riche sans exposer de type wx, Qt, base SQL ou chemin Windows. Il est porté par `domain.documents.DocumentModel` et reste sérialisable en JSON.

```text
DocumentModel
├── id                 UUID stable du document
├── format_version     1
├── document_type      code métier documentaire
├── html               HTML canonique nettoyé
├── metadata           métadonnées simples
├── assets             ressources identifiées et contrôlées
└── render_options     options JSON-compatibles
```

`format_version` est obligatoire. Un lecteur v1 refuse aujourd'hui une version inconnue plutôt que de l'interpréter silencieusement.

## Champs de fusion

La représentation canonique n'est pas une chaîne remplacée globalement. Un champ est un élément sémantique :

```html
<span data-pmsl-field="SALARIE_NOM">{SALARIE_NOM}</span>
```

Le texte visible à l'intérieur du `span` n'est pas l'identité du champ. L'identité est `data-pmsl-field` et doit exister dans le registre central avant d'être résolue.

Les syntaxes historiques telles que `{NOM}` sont reconnues par `domain.documents.legacy.upgrade_legacy_placeholders()` lorsqu'un alias est recensé. Un mot-clé inconnu est conservé tel quel. Les alias historiques qualifiés et les tokens volontairement non canoniques sont documentés dans `DOCUMENT_FIELD_LEGACY_ALIASES.md`.

## Sous-ensemble HTML v1

Le nettoyeur autorise notamment :

- paragraphes et blocs ;
- gras, italique, souligné et barré ;
- titres et listes ;
- tableaux ;
- liens `http`, `https`, `mailto`, `tel` et ancres locales ;
- images référencées par `asset://UUID` ;
- un sous-ensemble CSS de présentation ;
- propriétés de saut de page nécessaires au rendu imprimable.

Il supprime ou neutralise notamment le contenu actif, les gestionnaires `on*`, les protocoles dangereux, les images réseau implicites et le CSS actif/distant.

Le but n'est pas de devenir un navigateur HTML complet : le format est volontairement borné.

## Assets

Un asset v1 porte un UUID, un type MIME, un nom, un contenu base64 dans cette version, une empreinte SHA-256 et des métadonnées JSON-compatibles. Sa référence canonique est :

```text
asset://<uuid>
```

L'encodage base64 est un choix du format v1 autonome ; le contrat `asset://` permet une évolution ultérieure du stockage sans introduire aujourd'hui de GED ou de service dédié.

## Métadonnées et gouvernance

`DocumentMetadata.owner_domain` identifie le domaine propriétaire du document métier. Pour les documents RH traités ici, la valeur attendue est `rh`.

Ce champ ne décide pas du dossier de stockage, de l'original légal, de la durée de conservation ni de l'exposition Portail/NAS/GED. Ces décisions restent gouvernées hors du moteur documentaire.

## Import du patrimoine Teamword

Depuis l'itération 2, le lecteur direct TWD se trouve dans `infrastructure/documents/twd_importer.py`. Il lit le format wxWidgets RichText XML observé sans importer wxPython et produit un nouveau `DocumentModel v1` ; le `.twd` source reste intact.

Depuis l'itération 3, `infrastructure/documents/twd_compare.py` fournit un inventaire et un diff structurel pour comparer plusieurs générations réelles sans réduire la comparaison à un diff texte XML.

Ces composants sont **des adaptateurs legacy/infrastructure**. `domain.documents` ne dépend ni de wx, ni de Qt, ni de `GestionDB`, ni de l'UI Teamworks.

La qualification multi-version connue est décrite dans `TWD_MULTI_VERSION_AUDIT.md`. Elle ne vaut que pour les générations réellement disponibles et testées.

## Migration

Une migration est toujours une **copie vers un nouveau document** :

1. lecture du TWD ;
2. hash et inventaire du source ;
3. conversion vers le sous-ensemble HTML v1 et extraction des assets ;
4. sémantisation des seuls placeholders présents dans le registre ;
5. conservation et signalement des placeholders/structures non maîtrisés ;
6. sérialisation éventuelle du nouveau `DocumentModel`.

Aucune étape ne réécrit le TWD source. Cette itération n'active aucune migration en masse du patrimoine utilisateur.
