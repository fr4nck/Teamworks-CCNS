# Frais et déplacements

Teamworks-CCNS wx possède un onglet **Frais** dans la fiche individuelle et des dialogues dédiés à la gestion des frais, à la saisie d’un déplacement, à la saisie d’un remboursement et à l’impression des frais.

## Où trouver les frais ?

Ouvrez **Individus**, puis la fiche de la personne concernée et l’onglet **Frais**. Ce contexte garantit que les opérations affichées sont rattachées à la bonne personne.

## Déplacements et remboursements

Le dépôt contient les écrans `DLG_Saisie_deplacement.py` et `DLG_Saisie_remboursement.py`. Utilisez les actions proposées par l’onglet Frais pour créer/modifier les enregistrements plutôt que de manipuler directement la base.

## Impression

`DLG_Impression_frais.py` fournit la voie d’impression liée à ce module. Vérifiez la sélection et les montants avant de produire un justificatif définitif.

## Mots-clés de publipostage liés aux frais

Le moteur générique `UTILS_Publipostage_donnees.py` ne déclare **aucune catégorie `frais` ou `deplacement`**. Aucun mot-clé spécifique Frais/Déplacements n’est donc annoncé dans ce wiki sans preuve d’un autre moteur actif.

Les mots-clés Individu ne doivent pas être supposés disponibles depuis cet écran simplement parce qu’un frais appartient à une personne. Voir [[Mots-clés de publipostage]] pour les contextes réellement exposés.

## À documenter après validation fonctionnelle

Le détail des champs de déplacement, barèmes, calculs et cycle de remboursement doit être confirmé avec une recette fonctionnelle de l’interface wx avant d’être présenté comme procédure stable.
