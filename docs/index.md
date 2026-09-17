# Teamworks CCNS — Documentation

Cette documentation est la **source versionnée** du manuel Teamworks CCNS.

Les fichiers Markdown de `docs/` sont la source de vérité documentaire. MkDocs ne contient pas une seconde copie : il transforme ces mêmes fichiers en site web navigable et recherchable.

## Accès rapide

- [Guide utilisateur](utilisateur/index.md)
- [Publipostage et modèles de documents](utilisateur/publipostage.md)
- [Référence des mots-clés de publipostage](reference/mots-cles-publipostage.md)
- [Documentation technique et projet](README.md)

## Principe de maintenance

Une fonctionnalité documentée doit pointer vers la référence concernée plutôt que recopier une liste susceptible de diverger.

Pour le publipostage, la page de référence contient les mots-clés réellement exposés par le moteur actuel ainsi que leurs contextes d'utilisation. Les pages consacrées aux contrats, salariés, candidatures et documents doivent créer des liens vers ces ancres.

## Wiki GitHub

Le Wiki GitHub n'est pas la source canonique. S'il est conservé, il doit uniquement servir de redirection vers cette documentation afin d'éviter deux historiques divergents.

## Aide dans Teamworks

L'objectif est que l'aide contextuelle et l'éditeur interne Teamword renvoient vers les mêmes pages et les mêmes ancres. Le contenu ne doit donc pas être dupliqué dans l'application.
