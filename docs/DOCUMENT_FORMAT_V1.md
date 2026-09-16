# Format documentaire PMSL / Teamworks — version 1

Statut : **expérimental, première itération Qt**, non substitué aux modèles wx/TWD de production.

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

Les syntaxes historiques telles que `{NOM}` sont reconnues par l'adaptateur `domain.documents.legacy.upgrade_legacy_placeholders()` et converties vers la forme sémantique lorsqu'un alias est recensé. Un mot-clé inconnu est conservé tel quel.

## Sous-ensemble HTML v1

Le nettoyeur autorise notamment :

- paragraphes et blocs ;
- gras, italique, souligné et barré ;
- titres et listes ;
- tableaux ;
- liens `http`, `https`, `mailto`, `tel` et ancres locales ;
- images référencées par `asset://UUID` ;
- un sous-ensemble CSS de présentation ;
- propriétés de saut de page nécessaires au futur rendu imprimable.

Il supprime ou neutralise notamment :

- `script`, `iframe`, `object`, `embed`, contenu actif ;
- attributs d'événement `on*` ;
- protocoles dangereux ;
- images réseau implicites ;
- CSS contenant `url(...)`, `expression(...)`, `javascript:` ou `data:`.

Le but n'est pas de devenir un navigateur HTML complet : le format est volontairement borné.

## Assets

Un asset v1 porte :

- un UUID stable ;
- un type MIME ;
- un nom ;
- un contenu base64 dans cette première itération ;
- une empreinte SHA-256 ;
- des métadonnées JSON-compatibles.

Sa référence canonique est :

```text
asset://<uuid>
```

L'encodage base64 est un choix de prototype pour obtenir immédiatement un objet autonome et sérialisable. Il ne constitue pas une décision de stockage définitive. Le contrat `asset://` permet d'externaliser plus tard le stockage sans introduire aujourd'hui de GED ou de service dédié.

## Métadonnées et gouvernance

`DocumentMetadata.owner_domain` identifie le domaine propriétaire du document métier. Pour les documents RH traités ici, la valeur attendue est `rh`.

Ce champ ne décide pas :

- du dossier de stockage ;
- de l'original légal ;
- de la durée de conservation ;
- de l'exposition Portail/NAS/GED.

Ces décisions restent gouvernées par PMSL-Arch et ne sont pas encodées arbitrairement dans le moteur.

## Exemple JSON minimal

```json
{
  "id": "2c9415e4-4d0e-4aa3-9898-c319397178a7",
  "format_version": 1,
  "document_type": "contract",
  "html": "<p>Bonjour <span data-pmsl-field=\"SALARIE_PRENOM\">{SALARIE_PRENOM}</span></p>",
  "metadata": {
    "title": "Contrat",
    "owner_domain": "rh",
    "language": "fr-FR",
    "attributes": {}
  },
  "assets": [],
  "render_options": {
    "page_size": "A4"
  }
}
```

## Migration

La migration est toujours **copie vers un nouveau document**. Le fichier historique `.twd` / XML n'est jamais écrasé par le core.

La première itération fournit la conversion pure des mots-clés historiques une fois un contenu HTML obtenu. Le lecteur direct wx RichText XML/TWD reste à encapsuler dans une couche legacy dédiée : il n'est pas requis par le fonctionnement normal du core.
