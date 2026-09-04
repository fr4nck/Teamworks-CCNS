# Fondations UI Qt — Teamworks

## Intention

Le POC Qt transpose d’abord la composition et les repères fonctionnels de Teamworks wxPython avant toute modernisation visuelle plus ambitieuse.

Principes :

- fidélité à la disposition historique et aux regroupements métier ;
- adaptation propre aux contraintes de géométrie et de redimensionnement Qt ;
- lecture seule tant que les invariants métier et la persistance ne sont pas sécurisés ;
- aucune règle métier dans les widgets génériques ;
- aucune requête SQL ad hoc dans la couche Qt ;
- réutilisation des composants communs avant création de composants particuliers.

## Fondations communes

Les composants partagés vivent sous `ui/common/` :

- `TwDialogShell` pour la structure des dialogues ;
- `TwActionBar` pour les barres d’actions ;
- `TwFormSection` et `TwFieldRow` pour les formulaires ;
- `TwDataTable` pour les listes denses ;
- `TwCrudPanel` pour les ensembles liste + actions ;
- `TwSearchPicker` pour les recherches et sélections ;
- `TwChoiceStrip` pour les choix de mode exclusifs ;
- `validation.py` pour les états de validation ;
- `tokens.py` pour les dimensions et espacements communs.

Les règles métier restent dans les adaptateurs, contrôleurs ou modèles dédiés.

## Rail Individus / fiche individuelle

La fiche individuelle reprend les huit onglets historiques :

1. Généralités ;
2. Questionnaire ;
3. Qualifications ;
4. Contrats ;
5. Présences ;
6. Scénarios ;
7. Frais ;
8. Recrutement.

Le premier passage conserve les sections et l’ordre historique. Les pages Questionnaire, Qualifications, Présences et Recrutement individuel disposent déjà de leur composition Qt commune en lecture seule. Les pages Scénarios et Frais restent à transposer après caractérisation de leurs invariants historiques.

## Rail Recrutement global

L’espace Recrutement global est distinct de l’onglet Recrutement de la fiche individuelle. Il conserve la composition historique de `CTRL_Recrutement.py` :

- splitter vertical avec colonne de suivi à gauche et contenu principal à droite ;
- colonne gauche : `Prochains entretiens`, puis `À traiter` avec la description historique ;
- quatre modes : Candidats, Candidatures, Entretiens, Offres d’emploi ;
- une liste distincte par mode ;
- recherche visible uniquement en mode Candidats ;
- Courrier visible uniquement pour Candidats et Candidatures ;
- panneau `Détail de la sélection` masqué sans sélection ;
- sujet candidat/personne : onglets Identité, Candidatures, Entretiens ;
- sujet offre d’emploi : onglet Candidatures uniquement.

La sélection Qt s’appuie sur `recruitment_selection.py`, qui sépare explicitement la ligne cible des actions et le sujet affiché dans le résumé. Aucun candidat n’est implicitement converti en personne et aucune ligne métier fictive n’est injectée dans le POC.

La coque est exposée séparément par `run_windows.cmd recruitment`, conformément au caractère global de l’écran historique. Les données Recrutement et toutes les écritures restent non raccordées à ce stade.

## Rails de transposition en cours

Ordre retenu :

1. Recrutement global : coque historique et sélection typée ;
2. Scénarios : composition visuelle après caractérisation des dépendances et reports ;
3. Frais : composition visuelle après caractérisation des déplacements/remboursements ;
4. enrichissement progressif de Généralités et de ses satellites.

## Frugalité

Le POC conserve les budgets initiaux :

- premier affichage <= 3 s ;
- RSS <= 220 Mo ;
- dépendances UI directes <= 4.

Les lectures de production restent asynchrones lorsque leur coût peut bloquer le premier affichage.
