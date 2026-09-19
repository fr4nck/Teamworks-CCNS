# Individus et fiches

## À quoi ça sert ?

L'espace **Individus** est la liste centrale des personnes du dossier. Il permet de rechercher une personne, ouvrir sa fiche, produire des listes ou documents et contrôler rapidement l'état du dossier.

## Où la trouver ?

Onglet principal **Individus**. Une fiche s'ouvre avec **Ajouter**, **Modifier** ou un double-clic sur une ligne.

## Utiliser la liste

La page comprend la liste, un résumé de la sélection, une recherche texte et les actions **Ajouter**, **Modifier**, **Supprimer**, recherche par période de présence, **Tout afficher**, options/colonnes, courrier/publipostage, impression, export texte, export Excel et aide.

### Rechercher et trier

- Tapez un nom, prénom, ville ou autre texte dans **Rechercher un individu**.
- Cliquez sur un en-tête pour trier.
- Le bouton de recherche par période filtre les personnes présentes entre deux dates ; **Tout afficher** enlève ce filtre.
- **Export Excel** est désactivé sous Linux dans le contrôleur wx actuel ; l'export texte reste distinct.

## Personnaliser la liste {#personnaliser-liste}

Le bouton **Options** ouvre le dialogue de colonnes. Il permet :

- d'afficher ou masquer une colonne ;
- de déplacer une colonne vers le haut ou le bas ;
- de conserver l'ordre choisi ;
- de redimensionner directement les colonnes dans la liste ;
- de conserver le tri et les largeurs dans la configuration utilisateur.

Dans **Options**, utilisez **Réinitialiser** pour revenir aux colonnes, ordre et visibilité par défaut ; le contrôleur rétablit aussi les largeurs par défaut et le tri sur le nom croissant, puis mémorise ce nouvel état.

## Créer ou modifier une fiche

1. Dans **Individus**, cliquez sur **Ajouter** ou sélectionnez une ligne puis **Modifier**.
2. Complétez **Généralités** et validez les données nécessaires.
3. Utilisez ensuite les autres onglets selon le dossier.
4. Le passage hors de l'onglet Généralités sauvegarde ses données ; après cette première sauvegarde, l'annulation globale ne signifie plus qu'aucune donnée n'a été créée.

Une fiche neuve annulée avant toute sauvegarde est supprimée proprement (suppression atomique avec retour en arrière en cas d'erreur).

## Les huit onglets réels de la fiche individuelle {#onglets-fiche}

| Onglet affiché | Finalité et données principales | Actions confirmées dans le code |
|---|---|---|
| **Généralités** | identité, naissance, situation, adresse, coordonnées, mémo | saisir/modifier les champs ; assistance ville/pays ; coordonnées et mémo |
| **Questionnaire** | réponses au questionnaire configuré pour un individu | saisir les réponses ; certaines réponses peuvent référencer des documents. Formulaire statique — voir [FormEngine et questionnaires](../architecture/formengine-questionnaires.md) pour la nuance avec un futur moteur conditionnel |
| **Qualifications** | qualifications, pièces à fournir et pièces reçues | modifier les qualifications ; ajouter/modifier/supprimer une pièce reçue ; double-clic sur une pièce à fournir pour créer la pièce correspondante |
| **Contrats** | contrats rattachés à la personne | ajouter/modifier/supprimer ; marquer signature/DUE ; imprimer DUE ou un autre document — voir [Contrats, CCNS et CEE](contrats-ccns-cee.md) |
| **Présences** | présences de cette personne | ajouter/modifier/supprimer ; imprimer ; statistiques ; appliquer un modèle — voir [Présences et planning](presences-planning.md) |
| **Scénarios** | scénarios rattachés à la personne | panneau de gestion des scénarios ; comportement détaillé **à confirmer en recette fonctionnelle** |
| **Frais** | déplacements et remboursements | ajouter/modifier/supprimer ; imprimer les déplacements ; gérer les remboursements — voir [Frais et déplacements](frais-deplacements.md) |
| **Recrutement** | candidatures et entretiens déjà rattachés à l'individu | ajouter/modifier/supprimer candidature ou entretien — voir [Recrutement](recrutement.md) |

### Généralités : ce qui est réellement regroupé

Les éléments **Coordonnées**, **Situation** et **Mémo** ne sont pas des onglets séparés : ce sont des sections internes de **Généralités**. De même, qualifications, pièces à fournir et pièces reçues sont regroupées dans le seul onglet **Qualifications**. Ne cherchez pas d'onglet séparé pour ces éléments.

## Résultat attendu

Après validation, l'en-tête reprend l'identité, l'adresse, la naissance et la photo. La fiche expose ensuite les données liées à la personne dans chaque onglet.

## Données historiques incomplètes

La liste tolère certaines références anciennes manquantes et peut afficher **Pays introuvable (réf. …)**, **Nationalité introuvable**, **Situation introuvable** ou **Diplôme introuvable** au lieu de planter. Ces libellés signalent une donnée à corriger.

## Publipostage depuis Individus

Le bouton courrier lance le publipostage pour la sélection. Vérifiez les valeurs à l'étape **Vérification des données du document** avant fusion. Voir [Documents et publipostage](documents.md) et les [mots-clés du contexte Individu](../publipostage/contextes.md#individu-personne).

## Points d'attention

- La suppression d'une personne est destructive : sauvegardez avant une opération irréversible.
- Un numéro de sécurité sociale signalé comme valide par l'interface n'est pas une certification administrative.
- Les comportements fins des **Scénarios** restent **à confirmer en recette fonctionnelle**.

## Problèmes fréquents

Pour une fiche lente, une colonne illisible ou une référence introuvable, voir [Problèmes fréquents](../reference/problemes-frequents.md). Pour un crash, voir [Diagnostic et rapports de crash](../administration/diagnostic.md).

## Voir aussi

[Présences et planning](presences-planning.md) · [Contrats, CCNS et CEE](contrats-ccns-cee.md) · [Recrutement](recrutement.md) · [Frais et déplacements](frais-deplacements.md) · [Documents et publipostage](documents.md)
