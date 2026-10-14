# Modèles livrés et audit des balises

Teamworks-CCNS livre neuf modèles logiques d'exemple dans `teamworks/Static/Documents/`, déclinés selon les formats disponibles pour Teamword, Microsoft Word et LibreOffice Writer.

## Inventaire

| Modèle logique | Contexte de publipostage | .doc | .odt | .twd |
|---|---|:---:|:---:|:---:|
| Autorisation parentale mineurs - Exemple | Individu / salarié | ✓ | ✓ | ✓ |
| Certificat de travail - Exemple | Contrat | ✓ | ✓ | ✓ |
| Confirmation d'embauche - Exemple | Contrat | ✓ | ✓ | ✓ |
| Contrat d'engagement éducatif - Exemple | Contrat | ✓ | ✓ | ✓ |
| Contrat à durée déterminée - Exemple | Contrat | ✓ | ✓ | ✓ |
| Fiche candidature animateur - Exemple | Candidat | ✓ | ✓ | — |
| Fiche renseignements salarié - Exemple | Individu / salarié | ✓ | ✓ | — |
| Invitation réunion - Exemple | Individu | ✓ | ✓ | — |
| Lettre de refus - Exemple | Candidature | ✓ | ✓ | ✓ |

Cela représente **24 fichiers** : 9 modèles Word, 9 modèles LibreOffice et 6 modèles Teamword.

## Audit automatique

Le module `domain/documents/template_files.py` contrôle les balises sans démarrer d'application bureautique :

- les .twd sont lus comme documents XML Teamword ;
- les .odt sont ouverts comme archives OpenDocument et leurs fichiers XML sont inspectés ;
- les anciens .doc sont scannés pour les balises visibles en représentation ANSI et UTF-16LE.

Chaque modèle est audité avec son contexte réel afin de ne pas confondre les mots-clés Individu, Candidat, Candidature et Contrat.

Lorsqu'une variante .twd et une variante .odt existent pour le même modèle, la CI vérifie aussi qu'elles exposent le même contrat de balises. Cette comparaison vise à éviter qu'un modèle Teamword évolue sans son équivalent LibreOffice, ou inversement.

## Dette historique connue

Les modèles « Contrat d'engagement éducatif - Exemple » et « Contrat à durée déterminée - Exemple » contiennent historiquement les balises `{NBREJOURS}` et `{REPARTITION}`.

Ces noms ne correspondent à aucun mot-clé standard fourni par le moteur et aucun champ personnalisé portant ces noms n'est créé automatiquement sur une installation neuve. Ils restent donc considérés comme **balises inconnues tolérées explicitement** par le garde-fou, afin de préserver la compatibilité tout en rendant la dette visible.

Une troisième dette est détectée dans « Fiche renseignements salarié - Exemple » : les variantes Word et LibreOffice contiennent `{QUALIFICATIONS}`, alors que ce mot-clé appartient au contexte Candidat et n'est pas fourni par le contexte Individu/Salarié actuel. Le garde-fou conserve cette incohérence visible sans la corriger automatiquement.

Ces deux modèles utilisent également `{BRUTJOUR}`. Ce mot-clé est connu mais restreint au flux historique « Imprimer un document » depuis la fiche contrat, lorsqu'un barème CEE est disponible. Pour un modèle destiné à plusieurs points d'entrée, `{BAREMECEE}` est la clé plus générale.

## Ce que cet audit ne valide pas

L'audit statique ne prouve pas que Microsoft Word ou LibreOffice Writer savent ouvrir, modifier, fusionner, enregistrer ou imprimer le document sur le poste utilisateur.

Restent donc à qualifier séparément sur Windows :

- l'automatisation Word/COM ;
- l'automatisation LibreOffice/UNO ;
- le remplacement effectif des balises dans chaque moteur ;
- l'ouverture et l'enregistrement du fichier produit ;
- l'impression et les éventuelles conversions de format.

Le Rail C sépare volontairement ces opérations de l'analyse métier des données et des modèles.

## Voir aussi

[Référence des mots-clés](mots-cles.md) · [Contextes d'utilisation](contextes.md) · [Exemples](exemples.md) · [Documents et publipostage](../utilisation/documents.md)
