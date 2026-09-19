# Contrats, CCNS et CEE

Cette page décrit ce que Teamworks-CCNS calcule et affiche. Elle ne constitue pas un conseil juridique.

## A. Gestion d'un contrat

### Où la trouver ?

**Individus > ouvrir une fiche > onglet Contrats**.

### Comment l'utiliser ?

Dans l'onglet Contrats, les actions confirmées sont **Ajouter**, **Modifier**, **Supprimer**, bascule Signature, bascule/impression DUE et **Imprimer un document**. Un écran séparé, le **Registre unique du personnel**, liste tous les contrats de tous les individus avec aperçu, impression, publipostage et export.

L'assistant de création/modification comporte **6 pages** :

1. Écran d'accueil informatif.
2. Import éventuel d'un **modèle de contrat** préconfiguré.
3. L'essentiel métier : nature de l'opération (nouveau contrat, renouvellement CDD, passage CDD → CDI), contrat précédent si nécessaire, convention/régime, type de contrat, groupe CCNS ou qualification/statut CEE (mutuellement exclusifs), dates, durée hebdomadaire, rémunération, période d'essai.
4 et 5. Champs complémentaires historiques (choix puis saisie), masqués automatiquement lorsqu'ils sont déjà couverts nativement par le CCNS/CEE.
6. Validation finale.

Pour les parcours de renouvellement/passage CDD → CDI, le code exige un CDD précédent et contrôle la continuité de date.

Seules les conventions **CCNS**, et les types **CDD/CDI/CEE**, sont réellement raccordés au moteur de calcul détaillé ci-dessous ; les autres conventions (ÉCLAT, Centres sociaux, Autre) et types de contrat retombent sur le parcours historique (classification + valeur de point), sans contrôle CCNS/CEE automatique.

La période d'essai est proposée automatiquement selon des règles dépendant du groupe CCNS et du type d'opération (nouveau CDI/CDD, renouvellement, transformation) ; les cas non couverts restent **à confirmer en recette fonctionnelle**.

## B. Rémunération

Pour le régime CCNS, l'écran saisit une durée hebdomadaire et une rémunération brute mensuelle, ou une rémunération annuelle de référence lorsque le barème du groupe est annuel (groupes G7/G8). Le moteur recalcule l'aperçu de conformité en temps réel lorsque les données changent.

!!! info "Territoire SMIC figé sur la métropole"
    Le catalogue SMIC connaît un territoire Mayotte, mais l'assistant de création de contrat force toujours le territoire métropole : Mayotte n'est jamais sélectionnable depuis cet écran aujourd'hui.

## C. Contrôle CCNS {#controle-ccns}

Lorsque les données sont calculables, l'aperçu affiche :

- **Minimum CCNS** — calculé depuis la grille du groupe (G1 à G6, valeurs mensuelles), proratisé selon la durée hebdomadaire par rapport à un temps plein de 35 h, avec une majoration temps partiel (5 % en dessous de 10 h, 2 % entre 10 h et 24 h, 0 % au-delà) ;
- **Minimum SMIC** — proratisé selon la durée hebdomadaire, **sans** majoration temps partiel (contrairement au CCNS) ;
- **Minimum retenu** et sa source (CCNS, SMIC, ou égalité) — le plus élevé des deux ;
- état **CONFORME** ou **NON CONFORME** avec l'écart, pour les groupes à minimum mensuel (G1-G6).

!!! warning "Blocage réel à l'enregistrement"
    Pour un groupe à minimum mensuel (G1-G6), une rémunération non conforme **empêche l'enregistrement du contrat** — ce n'est pas un simple message informatif.

Pour un groupe à minimum annuel (G7/G8), l'interface affiche **« Contrôle annuel requis »** plutôt qu'un statut conforme/non conforme automatique, et n'applique pas de prorata selon les heures pour ces groupes.

!!! info "Un second moteur de contrôle, en lot"
    Un moteur d'audit distinct parcourt l'ensemble des contrats du dossier (accessible depuis les écrans d'audit CCNS) et peut s'appuyer sur des grilles salariales stockées en base plutôt que sur la grille figée utilisée par l'aperçu de l'assistant ; il ajoute aussi un contrôle d'ancienneté CCNS. Son rendu exact (menus, tableaux) reste **à confirmer en recette fonctionnelle** dans le cadre de cette documentation.

## D. Contrôle CEE

Le régime CEE utilise la qualification/statut CEE, une date de référence et un barème employeur optionnel (configuré dans **Paramétrage > Barèmes CEE**, par qualification et date d'effet). Le minimum légal journalier CEE est calculé à partir du SMIC horaire métropole et d'un coefficient réglementaire qui a changé dans le temps.

- Si aucun barème employeur n'est configuré : seul le minimum légal est affiché, sans statut conforme/non conforme.
- Si un barème existe : conforme si le montant employeur est au moins égal au minimum légal.

!!! info "Pas de blocage à l'enregistrement pour le CEE"
    Contrairement au CCNS, aucun blocage n'a été trouvé dans le code pour un barème CEE non conforme au minimum légal — seule la sélection de la qualification est obligatoire. **À confirmer en recette fonctionnelle** si un blocage est réellement attendu.

## E. Compatibilité historique

Les anciens dossiers/modèles peuvent encore utiliser `CLASSIFICATION` et `VALEURPOINT`. Le champ historique `BRUTMENS` (avec `HEBDO`/`ANNUEL`) **n'est pas un alias** qui recopie `SALAIREBRUTMENSUEL` : c'est un champ de contrat devenu redondant, simplement masqué de la liste des compléments optionnels lorsque la convention CCNS est sélectionnée. Le seul alias réellement implémenté est `{BRUTJOUR}` → `{BAREMECEE}`, disponible uniquement depuis le bouton **Imprimer un document** de l'onglet Contrats — voir la [référence des mots-clés](../publipostage/mots-cles.md#publipostage-brutjour).

Les contrats modernes privilégient les champs CCNS/CEE structurés. L'assistant masque certains anciens champs complémentaires lorsqu'ils sont déjà gérés nativement.

## Lecture d'un résultat de conformité

| Élément | Lecture utilisateur |
|---|---|
| **Minimum CCNS** | minimum calculé à partir du groupe/barème CCNS applicable lorsque le moteur dispose des données nécessaires |
| **Minimum SMIC** | minimum issu du catalogue SMIC utilisé par le moteur pour le territoire pris en charge (métropole, dans l'assistant de contrat) |
| **Minimum retenu** | le montant que le moteur retient comme seuil de comparaison entre les minima disponibles |
| **CONFORME** | la rémunération saisie atteint le minimum retenu dans le calcul effectué |
| **NON CONFORME** | la rémunération saisie est inférieure au minimum retenu ; l'interface indique l'écart et bloque l'enregistrement (groupes mensuels) |
| **Contrôle annuel requis** | le barème est annuel (G7/G8) et ne doit pas être lu comme un simple contrôle mensuel |
| **Non calculable** | données absentes/incompatibles : groupe, date, qualification, barème ou rémunération à vérifier |

Ce résultat est un calcul logiciel sur les données saisies, pas une certification juridique du contrat.

## Documents et DPAE/DUE

Depuis l'onglet Contrats, **Imprimer** peut ouvrir l'édition DUE ou un document de contrat (avec, dans ce cas, l'alias `{BRUTJOUR}` et la [couche moderne RH](../publipostage/mots-cles.md#couche-moderne-rh) en plus). Voir [DPAE et DUE](dpae-due.md) et [Documents et publipostage](documents.md).

## Mots-clés

Un contexte Contrat reçoit les 18 mots-clés de l'individu titulaire, puis ceux du contrat. Références utiles : [`{DATEDEBUT}`](../publipostage/mots-cles.md#publipostage-datedebut), [`{SALAIREBRUTMENSUEL}`](../publipostage/mots-cles.md#publipostage-salairebrutmensuel), [`{MINIMUMCCNS}`](../publipostage/mots-cles.md#publipostage-minimumccns), [`{MINIMUMSMIC}`](../publipostage/mots-cles.md#publipostage-minimumsmic), [`{MINIMUMRETENU}`](../publipostage/mots-cles.md#publipostage-minimumretenu), [`{CONFORMITEREMUNERATION}`](../publipostage/mots-cles.md#publipostage-conformiteremuneration), [`{BAREMECEE}`](../publipostage/mots-cles.md#publipostage-baremecee), [`{MINIMUMCEE}`](../publipostage/mots-cles.md#publipostage-minimumcee).

## Points d'attention

- Une donnée vide dans le document peut signaler un calcul impossible, pas une panne de publipostage.
- Les valeurs historiques restent utiles pour les anciens modèles mais ne doivent pas être confondues avec le moteur actuel.
- Les contrôles métier nécessitant une vraie situation employeur restent **à confirmer en recette fonctionnelle**.

## Voir aussi

[Individus et fiches](individus.md) · [DPAE et DUE](dpae-due.md) · [Référence des mots-clés](../publipostage/mots-cles.md) · [Paramétrage](../administration/parametrage.md)
