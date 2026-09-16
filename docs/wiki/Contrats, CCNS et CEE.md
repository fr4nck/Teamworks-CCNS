# Contrats, CCNS et CEE

Cette page décrit ce que Teamworks-CCNS calcule et affiche. Elle ne constitue pas un conseil juridique.

<a id="gestion-contrat"></a>
## A. Gestion d’un contrat

### Où la trouver ?

**Individus > ouvrir une fiche > Contrats**.

### Comment l’utiliser ?

Dans l’onglet Contrats, les actions confirmées sont **Ajouter**, **Modifier**, **Supprimer**, suivi de signature/DUE et impression. L’assistant de création/modification comporte six pages internes et collecte notamment :

- nature de l’opération : nouveau contrat, renouvellement CDD, passage CDD → CDI ;
- contrat précédent lorsque nécessaire ;
- convention/régime ;
- type de contrat ;
- groupe CCNS ou qualification/statut CEE ;
- dates ;
- durée hebdomadaire ;
- rémunération ;
- période d’essai ;
- informations complémentaires éventuelles.

Pour les parcours de renouvellement/passage CDD → CDI, le code exige un CDD précédent et contrôle la continuité de date.

<a id="remuneration"></a>
## B. Rémunération

Pour le régime CCNS, l’écran saisit une durée hebdomadaire et une rémunération brute mensuelle, ou une rémunération annuelle de référence lorsque le barème du groupe est annuel. Le moteur peut préremplir un minimum calculé et recalcule l’aperçu de conformité lorsque les données changent.

<a id="controle-ccns"></a>
## C. Contrôle CCNS

Lorsque les données sont calculables, l’aperçu affiche :

- **Minimum CCNS** ;
- **SMIC** ;
- **Minimum retenu** et sa source ;
- état **CONFORME** ou **NON CONFORME** avec l’écart.

Pour une grille à minimum annuel, l’interface affiche un minimum annuel de référence et avertit qu’une période incomplète nécessite un prorata. Le moteur ne doit pas être présenté comme transformant automatiquement tous les cas annuels en équivalent mensuel universel.

<a id="controle-cee"></a>
## D. Contrôle CEE

Le régime CEE utilise la qualification/statut CEE, une date de référence et le barème disponible. Teamworks peut afficher le minimum journalier et le barème applicable lorsque les données permettent le calcul.

**À confirmer en recette fonctionnelle :** le parcours complet de tous les cas CEE réels et le rendu utilisateur pour chaque qualification/barème.

<a id="compatibilite-historique"></a>
## E. Compatibilité historique

Les anciens dossiers/modèles peuvent encore utiliser :

- `CLASSIFICATION` ;
- `VALEURPOINT` ;
- `BRUTMENS`, alias de compatibilité de `SALAIREBRUTMENSUEL`.

Les contrats modernes privilégient les champs CCNS/CEE structurés. L’assistant masque certains anciens champs complémentaires lorsqu’ils sont déjà gérés nativement.

<a id="lecture-conformite"></a>
## Lecture d’un résultat de conformité

| Élément | Lecture utilisateur |
|---|---|
| **Minimum CCNS** | minimum calculé à partir du groupe/barème CCNS applicable lorsque le moteur dispose des données nécessaires |
| **Minimum SMIC** | minimum issu du catalogue SMIC utilisé par le moteur pour le territoire pris en charge |
| **Minimum retenu** | le montant que le moteur retient comme seuil de comparaison entre les minima disponibles |
| **CONFORME** | la rémunération saisie atteint le minimum retenu dans le calcul effectué |
| **NON CONFORME** | la rémunération saisie est inférieure au minimum retenu ; l’interface indique l’écart |
| **Contrôle annuel requis** | le barème est annuel et ne doit pas être lu comme un simple contrôle mensuel |
| **Non calculable** | données absentes/incompatibles : groupe, date, qualification, barème ou rémunération à vérifier |

Ce résultat est un calcul logiciel sur les données saisies, pas une certification juridique du contrat.

## Documents et DPAE/DUE

Depuis l’onglet Contrats, **Imprimer** peut ouvrir l’édition DUE ou un document de contrat. Voir [[DPAE et DUE]] et [[Publipostage et documents]].

## Mots-clés

Un contexte Contrat reçoit les données de l’individu puis celles du contrat. Références utiles : [`{DATEDEBUT}`](Mots-clés-de-publipostage#publipostage-datedebut), [`{SALAIREBRUTMENSUEL}`](Mots-clés-de-publipostage#publipostage-salairebrutmensuel), [`{MINIMUMCCNS}`](Mots-clés-de-publipostage#publipostage-minimumccns), [`{MINIMUMSMIC}`](Mots-clés-de-publipostage#publipostage-minimumsmic), [`{MINIMUMRETENU}`](Mots-clés-de-publipostage#publipostage-minimumretenu), [`{CONFORMITEREMUNERATION}`](Mots-clés-de-publipostage#publipostage-conformiteremuneration).

## Points d’attention

- Une donnée vide dans le document peut signaler un calcul impossible, pas une panne de publipostage.
- Les valeurs historiques restent utiles pour les anciens modèles mais ne doivent pas être confondues avec le moteur actuel.
- Les contrôles métier nécessitant une vraie situation employeur restent **À confirmer en recette fonctionnelle**.

## Liens associés

[[Individus et fiches]] · [[DPAE et DUE]] · [[Mots-clés de publipostage]] · [[Paramétrage]]
